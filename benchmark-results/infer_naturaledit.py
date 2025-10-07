from typing import Iterable, Dict
import openai
from tqdm import tqdm
import os
import re
import argparse
import json
import gzip
from concurrent.futures import ThreadPoolExecutor

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def stream_jsonl(filename: str) -> Iterable[Dict]:
    """
    Parses each jsonl line and yields it as a dictionary
    """
    if filename.endswith(".gz"):
        with open(filename, "rb") as gzfp:
            with gzip.open(gzfp, "rt") as fp:
                for line in fp:
                    if any(not x.isspace() for x in line):
                        yield json.loads(line)
    else:
        with open(filename, "r") as fp:
            for line in fp:
                if any(not x.isspace() for x in line):
                    yield json.loads(line)


def write_jsonl(filename: str, data: Iterable[Dict], append: bool = False):
    """
    Writes an iterable of dictionaries to jsonl
    """
    if append:
        mode = "ab"
    else:
        mode = "wb"
    filename = os.path.expanduser(filename)
    if filename.endswith(".gz"):
        with open(filename, mode) as fp:
            with gzip.GzipFile(fileobj=fp, mode="wb") as gzfp:
                for x in data:
                    gzfp.write((json.dumps(x) + "\n").encode("utf-8"))
    else:
        with open(filename, mode) as fp:
            for x in data:
                fp.write((json.dumps(x) + "\n").encode("utf-8"))


def get_code_summary_prompt(code):
    return f"""
You are an expert code summarizer. For the following code, generate 6 summaries, one for each combination of detail level (low, medium, high) and structure (unstructured, i.e., paragraph, structured, i.e., bulleted):
- low_unstructured: One-sentence, low-detail, paragraph style.
- low_structured: 2-3 short bullet points, low-detail, as a single string. Each bullet must start with "•" and be separated by \\n. Never return an array.
- medium_unstructured: 2-3 sentences, medium-detail, paragraph style.
- medium_structured: 3-5 bullet points, medium-detail, as a single string. Use "•" for first-level bullets, and ENCOURAGE the use of two-level bullets (use "◦" for the second level, and indent the second-level bullet with 2 spaces before the "◦") when logical groupings exist. Bullets must be separated by \\n. Never return an array.
- high_unstructured: 3-4 sentences, high-detail, paragraph style.
- high_structured: 4-8 bullet points, high-detail, as a single string. Use "•" for first-level bullets, and ENCOURAGE the use of two-level bullets (use "◦" for the second level, and indent the second-level bullet with 2 spaces before the "◦") when logical groupings exist. Bullets must be separated by \\n. Never return an array.

IMPORTANT:
- For medium_structured and high_structured, if there are logical groupings, you should use two-level bullets ("•" and "◦"). For the second-level bullet ("◦"), always indent with 2 spaces before the "◦".
- The file context below is provided ONLY for reference to help understand the code's environment.
- Your summary MUST focus ONLY on the specific code snippet provided.
- Return your response as a JSON object with keys: title, low_unstructured, low_structured, medium_unstructured, medium_structured, high_unstructured, high_structured.

Code to summarize:
{code}

Summary:
"""


def get_apply_direct_on_summary_prompt(original_code, original_summary, instruction):
    return f"""
You are an expert at editing code summaries. In this scenario, a developer is using a summary-mediated approach to modify code:
1. Instead of directly editing the code, the developer modifies the summary to express their desired code behavior.
2. The modified summary will later be used to generate the actual code changes.
3. Your task is to integrate the developer's instruction into the summary, making it clear what the new code should do.

Given the following original summary and a direct instruction, update the summary to incorporate the developer's intent:
- The code context below is provided ONLY for reference to help understand the summary's environment.
- Preserve the parts of the original summary that are not affected by the instruction.
- Maintain the original summary format (sentence, bullet points, etc.).
- Make it easy to identify what changed by keeping unchanged parts exactly as they were.
- Integrate the instruction seamlessly into existing sentences or bullet points as much as possible.
- However, add new sentences or bullet points if the instruction cannot be naturally integrated into existing ones.
- The updated summary MUST clearly express what the new code should do, incorporating ALL information from the instruction.
- Output only the updated summary, nothing else.

Code Context (for reference only):
{original_code}

Original summary:
{original_summary}

Developer's instruction (integrate this intent fully into the updated summary):
{instruction}

Updated summary:
"""


def get_direct_instruction_prompt(original_code, instruction):
    return f"""
You are an expert code editor. Given the following original code and a direct instruction, update the code to fulfill the instruction.
- Only change the code as needed to satisfy the instruction, and keep the rest of the code unchanged.
- Output only the updated code wrapped in ```python and ```, nothing else. However, the parts of the original code that need to be retained must be re-output completely and not omitted (e.g., import statements).

Original code:
{original_code}

Instruction:
{instruction}

Updated code:
"""


def get_summary_mediated_prompt(original_code, edited_summary, original_summary):
    return f"""
You are an expert code editor. Given the following original code and an updated summary, update the code to reflect the changes in the new summary.
- Only change the code as needed to match the new summary, and keep the rest of the code unchanged.
- Pay close attention to the differences between the original summary and the edited summary, which reflects developer's intent of what the new code should be.
- Output only the updated code wrapped in ```python and ```, nothing else. However, the parts of the original code that need to be retained must be re-output completely and not omitted (e.g., import statements).

Original code:
{original_code}

Original summary:
{original_summary}

Updated summary:
{edited_summary}

Updated code:
"""


def gpt_completion(prompt, model="gpt-3.5-turbo"):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=4096,
    )
    return response.choices[0].message.content


def extract_code(text):
    match = re.search(r"```[\w]*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


if __name__ == "__main__":
    # Parse command line arguments for dataset, model, and task
    parser = argparse.ArgumentParser(
        description="Run code editing tasks with different models and datasets."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        choices=["EditEval", "CanItEdit"],
        help="Dataset to use (EditEval or CanItEdit)",
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        choices=["gpt-3.5-turbo", "gpt-4o", "gpt-4.1"],
        help="Model to use (gpt-3.5-turbo, gpt-4o, or gpt-4.1)",
    )
    parser.add_argument(
        "--task",
        type=str,
        required=True,
        choices=["direct_instruction", "summary_mediated"],
        help="Task type (direct_instruction or summary_mediated)",
    )
    parser.add_argument(
        "--type",
        type=str,
        required=False,
        choices=["descriptive", "lazy"],
        help="Instruction type in CanItEdit (descriptive or lazy)",
    )
    args = parser.parse_args()

    input_file = f"data/{args.dataset}.jsonl"
    output_file = (
        f"output/{args.dataset}_{args.model}_{args.task}"
        + (f"_{args.type}" if args.type is not None else "")
        + ".jsonl"
    )

    if args.dataset == "CanItEdit":
        INPUT, OUTPUT, INSTRUCTION, TEST = (
            "before",
            "after",
            f"instruction_{args.type}",
            "tests",
        )
        assert INSTRUCTION in ["instruction_lazy", "instruction_descriptive"]
    elif args.dataset == "EditEval":
        INPUT, OUTPUT, INSTRUCTION, TEST = "input", "output", "instruction", "test"

    BATCH_SIZE = 20

    def process_sample(sample):
        try:
            if args.task == "direct_instruction":
                prompt = get_direct_instruction_prompt(
                    sample[INPUT], sample[INSTRUCTION]
                )
                sample["output"] = extract_code(gpt_completion(prompt, args.model))
            elif args.task == "summary_mediated":
                # All summary-related fields (original_summary, edited_summary, output) are now dicts,
                # with keys: low_unstructured, low_structured, medium_unstructured, medium_structured, high_unstructured, high_structured.
                # Each summary type is processed independently.
                prompt = get_code_summary_prompt(sample[INPUT])
                summary_json = gpt_completion(prompt, args.model)
                try:
                    sample["original_summary"] = json.loads(summary_json)
                except Exception as e:
                    # Log summary JSON parse error
                    return None

                # Apply instruction to each summary type (except title) in parallel
                sample["edited_summary"] = {}
                with ThreadPoolExecutor(max_workers=6) as executor:
                    futures = {
                        k: executor.submit(
                            gpt_completion,
                            get_apply_direct_on_summary_prompt(
                                sample[INPUT], v, sample[INSTRUCTION]
                            ),
                            args.model,
                        )
                        for k, v in sample["original_summary"].items()
                        if k != "title"
                    }
                    for k, future in futures.items():
                        sample["edited_summary"][k] = future.result()
                # Copy title if present
                if "title" in sample["original_summary"]:
                    sample["edited_summary"]["title"] = sample["original_summary"][
                        "title"
                    ]

                # Generate code for each summary type (except title) in parallel
                sample["output"] = {}
                with ThreadPoolExecutor(max_workers=6) as executor:
                    futures = {
                        k: executor.submit(
                            gpt_completion,
                            get_summary_mediated_prompt(
                                sample[INPUT],
                                sample["edited_summary"][k],
                                sample["original_summary"][k],
                            ),
                            args.model,
                        )
                        for k in sample["original_summary"]
                        if k != "title"
                    }
                    for k, future in futures.items():
                        sample["output"][k] = extract_code(future.result())
            return sample
        except Exception as e:
            # Log error for this sample, but do not print intermediate state
            return None

    all_samples = list(stream_jsonl(input_file))
    results = []
    for i in tqdm(range(0, len(all_samples), BATCH_SIZE), desc="Processing batches"):
        batch = all_samples[i : i + BATCH_SIZE]
        with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
            futures = [executor.submit(process_sample, sample) for sample in batch]
            for future in futures:
                result = future.result()
                if result is not None:
                    results.append(result)

    write_jsonl(output_file, results)
    print(f"Done! Results saved to {output_file}")
