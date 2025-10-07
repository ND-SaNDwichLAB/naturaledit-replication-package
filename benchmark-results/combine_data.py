import argparse
import json
import os

# =========================
# Argument Parsing
# =========================


def parse_args():
    parser = argparse.ArgumentParser(
        description="Combine and normalize evaluation data for CanItEdit/EditEval."
    )
    parser.add_argument(
        "--dataset",
        required=True,
        choices=["CanItEdit", "EditEval"],
        help="Dataset name",
    )
    parser.add_argument(
        "--model",
        required=True,
        choices=["gpt-4o", "gpt-3.5-turbo", "gpt-4.1"],
        help="Model name",
    )
    parser.add_argument(
        "--type",
        required=True,
        help="Type: For CanItEdit: descriptive/lazy; For EditEval: instruction",
    )
    parser.add_argument("--output", default=None, help="Output file path (optional)")
    return parser.parse_args()


# =========================
# File Path Construction
# =========================


def get_file_paths(dataset, model, type_):
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "data")
    output_dir = os.path.join(base_dir, "output")

    if dataset == "CanItEdit":
        base_file = os.path.join(data_dir, "CanItEdit.jsonl")
        direct_output = os.path.join(
            output_dir, f"CanItEdit_{model}_direct_instruction_{type_}.jsonl"
        )
        direct_results = os.path.join(
            output_dir,
            f"CanItEdit_{model}_direct_instruction_{type_}.jsonl_results.jsonl",
        )
        summary_output = os.path.join(
            output_dir, f"CanItEdit_{model}_summary_mediated_{type_}.jsonl"
        )
        summary_results = os.path.join(
            output_dir,
            f"CanItEdit_{model}_summary_mediated_{type_}.jsonl_results.jsonl",
        )
    else:
        base_file = os.path.join(data_dir, "EditEval.jsonl")
        direct_output = os.path.join(
            output_dir, f"EditEval_{model}_direct_instruction.jsonl"
        )
        direct_results = os.path.join(
            output_dir, f"EditEval_{model}_direct_instruction.jsonl_results.jsonl"
        )
        summary_output = os.path.join(
            output_dir, f"EditEval_{model}_summary_mediated.jsonl"
        )
        summary_results = os.path.join(
            output_dir, f"EditEval_{model}_summary_mediated.jsonl_results.jsonl"
        )

    return {
        "base": base_file,
        "direct_output": direct_output,
        "direct_results": direct_results,
        "summary_output": summary_output,
        "summary_results": summary_results,
    }


# =========================
# Data Loading
# =========================


def load_jsonl(path, is_summary_results=False):
    data = {}
    if not os.path.exists(path):
        return data
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                if is_summary_results and "id" in obj and "level" in obj:
                    key = int(obj["id"])
                    level = obj["level"]
                    if key not in data:
                        data[key] = {}
                    data[key][level] = obj
                else:
                    # Use id or task_id as key
                    if "id" in obj:
                        key = int(obj["id"])
                    elif "task_id" in obj:
                        key = int(str(obj["task_id"]).split("/")[-1])
                    else:
                        continue
                    data[key] = obj
    return data


# =========================
# Normalization Functions
# =========================


def normalize_canitedit(obj, type_):
    return {
        "id": obj["id"],
        "name": obj.get("name", ""),
        "buggy_code": obj.get("before", ""),
        "ground_truth": obj.get("after", ""),
        "tests": obj.get("tests", ""),
        "instruction": obj.get(f"instruction_{type_}", ""),
    }


def normalize_editeval(obj):
    # "task_id": "EditEval/0" → id: 0
    id_ = int(str(obj["task_id"]).split("/")[-1])
    return {
        "id": id_,
        "name": "",
        "buggy_code": obj.get("input", ""),
        "ground_truth": obj.get("output", ""),
        "tests": obj.get("test", ""),
        "instruction": obj.get("instruction", ""),
    }


# =========================
# Merge All Data
# =========================


def merge_all(
    base_data,
    direct_outputs,
    direct_results,
    summary_outputs,
    summary_results,
    dataset,
    type_,
):
    merged = []
    for id_ in base_data:
        if dataset == "CanItEdit":
            base = normalize_canitedit(base_data[id_], type_)
        else:
            base = normalize_editeval(base_data[id_])

        # Direct output/result
        direct_out = direct_outputs.get(id_, {})
        direct_res = direct_results.get(id_, {})
        base["output_direct"] = direct_out.get("output", "")
        base["result_direct"] = direct_res.get("result", "")
        base["error_direct"] = direct_res.get("error", "")

        # Summary-mediated output/result
        summary_out = summary_outputs.get(id_, {})
        summary_res = summary_results.get(id_, {})

        base["original_summary"] = summary_out.get("original_summary", {})
        base["edited_summary"] = summary_out.get("edited_summary", {})

        # output_summary, result_summary, error_summary: dict per summary level
        base["output_summary"] = {}
        base["result_summary"] = {}
        base["error_summary"] = {}

        output_dict = summary_out.get("output", {})
        if isinstance(output_dict, dict):
            for level in output_dict:
                base["output_summary"][level] = output_dict.get(level, "")
                if level in summary_res:
                    base["result_summary"][level] = summary_res[level].get("result", "")
                    base["error_summary"][level] = summary_res[level].get("error", "")
                else:
                    base["result_summary"][level] = ""
                    base["error_summary"][level] = ""
        else:
            base["output_summary"] = output_dict
            base["result_summary"] = summary_res.get("result", "")
            base["error_summary"] = summary_res.get("error", "")

        merged.append(base)
    return merged


# =========================
# Main
# =========================


def main():
    args = parse_args()
    dataset = args.dataset
    model = args.model
    type_ = args.type
    output_path = args.output or f"output/combined/{dataset}_{model}_{type_}.jsonl"

    # File paths
    paths = get_file_paths(dataset, model, type_)

    # Load all data
    base_data = load_jsonl(paths["base"])
    direct_outputs = load_jsonl(paths["direct_output"])
    direct_results = load_jsonl(paths["direct_results"])
    summary_outputs = load_jsonl(paths["summary_output"])
    summary_results = load_jsonl(paths["summary_results"], is_summary_results=True)

    # Merge
    merged = merge_all(
        base_data,
        direct_outputs,
        direct_results,
        summary_outputs,
        summary_results,
        dataset,
        type_,
    )

    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        for obj in merged:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    print(f"Combined data written to {output_path}")


if __name__ == "__main__":
    main()
