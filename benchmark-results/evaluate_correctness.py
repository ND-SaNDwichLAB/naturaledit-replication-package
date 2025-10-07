import json
import tqdm
import warnings
import argparse
import sys
import io
import contextlib
import multiprocessing


warnings.filterwarnings("ignore")


def build_code_to_run(after_code: str, test_code: str, task_id: int, dataset_name: str):
    if dataset_name == "CanItEdit":
        if task_id in [38, 54]:
            with open(f"data/{task_id}.test", "r", encoding="utf-8") as f:
                test_code = f.read()
        elif task_id == 78 and sys.platform == "darwin":
            return None  # vllm skip on MacOS
        return (after_code + "\n\n" + test_code).strip()
    else:
        return (after_code + "\n\n" + test_code + "\n\ncheck()").strip()


def _exec_code(code: str, queue):
    """
    Execute the given code in a separate process and capture exceptions.
    """
    try:
        exec_globals = {}
        with contextlib.redirect_stdout(io.StringIO()):
            exec(code, exec_globals)
        queue.put((True, ""))  # Pass, no error
    except Exception as e:
        queue.put((False, str(e)))  # Fail, capture error message


def run_entry(code_to_run: str):
    """
    Run the code and return (result, error_message).
    """
    if code_to_run is None:
        return False, "Skipped (code_to_run is None)"

    queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=_exec_code, args=(code_to_run, queue))
    p.start()
    p.join(timeout=30)

    if p.is_alive():
        p.terminate()
        p.join()
        return False, "Timeout"

    if not queue.empty():
        return queue.get()
    else:
        return False, "Unknown error"


from concurrent.futures import ThreadPoolExecutor, as_completed


def run_all_from_jsonl(jsonl_path: str, save_results: bool = False):
    """
    Run all entries from the JSONL file, print summary, and optionally save results.
    For summary-mediated tasks, evaluates and reports correctness for each summary type separately.
    """
    dataset_name = jsonl_path.split("/")[-1].split(".")[0].split("_")[0]
    assert dataset_name in ["CanItEdit", "EditEval"]
    if jsonl_path.split("/")[-2] == "output":
        method_name = " ".join(jsonl_path.split("/")[-1][:-5].split("_")[1:])
    else:
        method_name = "groundtruth"
    print(f"Running {dataset_name} with {method_name}")

    results = {}
    results_to_save = []

    # Read all data first
    with open(jsonl_path, "r", encoding="utf-8") as f:
        all_lines = [line for line in f if line.strip()]
    total_tasks = 0
    eval_tasks = []
    for line in all_lines:
        data = json.loads(line)
        if dataset_name == "CanItEdit":
            if "output" not in data.keys():
                data["output"] = data["after"]
            sample_id = data["id"]
            test_code = data["tests"]
        else:
            data["id"] = data["task_id"].split("/")[1]
            sample_id = data["id"]
            CODE_MARKER = r"{{Code}}"
            if "context" in data.keys() and CODE_MARKER in data["context"]:
                if isinstance(data["output"], dict):
                    data["output"] = {
                        k: data["context"].replace(CODE_MARKER, v)
                        for k, v in data["output"].items()
                    }
                else:
                    data["output"] = data["context"].replace(
                        CODE_MARKER, data["output"]
                    )
            test_code = data["test"]

        # If output is dict, evaluate all levels
        if isinstance(data["output"], dict):
            for level, code in data["output"].items():
                eval_tasks.append(
                    (sample_id, level, code, test_code, sample_id, dataset_name)
                )
                if level not in results:
                    results[level] = {"PASS": [], "FAIL": []}
                total_tasks += 1
        else:
            eval_tasks.append(
                (
                    sample_id,
                    "single",
                    data["output"],
                    test_code,
                    sample_id,
                    dataset_name,
                )
            )
            if "single" not in results:
                results["single"] = {"PASS": [], "FAIL": []}
            total_tasks += 1

    def evaluate_one(sample_id, level, code, test_code, task_id, dataset_name):
        code_to_run = build_code_to_run(code, test_code, task_id, dataset_name)
        result, error_msg = run_entry(code_to_run)
        key = "PASS" if result else "FAIL"
        return {"id": sample_id, "level": level, "result": key, "error": error_msg}

    # Parallel evaluation
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(evaluate_one, *args) for args in eval_tasks]
        for f in tqdm.tqdm(as_completed(futures), total=total_tasks, desc="Evaluating"):
            entry = f.result()
            level = entry["level"]
            key = entry["result"]
            results[level][key].append(entry["id"])
            if save_results:
                results_to_save.append(entry)

    for level in results:
        num_pass = len(results[level]["PASS"])
        num_fail = len(results[level]["FAIL"])
        total = num_pass + num_fail
        print(f"Summary type: {level}")
        print(
            f"PASS: {num_pass}/{total} ({(num_pass / total * 100) if total > 0 else 0:.2f}%)"
        )
        print(f"FAIL: {num_fail}/{total}")
        print()

    # Save results to file if requested
    if save_results:
        output_path = jsonl_path + "_results.jsonl"
        with open(output_path, "w", encoding="utf-8") as fout:
            for entry in results_to_save:
                fout.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"Results saved to {output_path}")


def main(jsonl_path: str, save_results: bool = False):
    """
    Main entry point for running evaluation.
    """
    run_all_from_jsonl(jsonl_path, save_results=save_results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run all entries from a JSONL file and show progress."
    )
    parser.add_argument("jsonl_path", type=str, help="Path to the input JSONL file.")
    parser.add_argument(
        "--save_results", action="store_true", help="Save results to a JSONL file."
    )
    args = parser.parse_args()
    main(args.jsonl_path, save_results=args.save_results)
