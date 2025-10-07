import os
import json
import re
from typing import List, Dict, Any
from openai import OpenAI


def clean_llm_code_block(content: str) -> str:
    """
    Remove all code block markers (e.g., ``` or ```python) from LLM output.
    This function ensures only the code or summary content remains.

    Args:
        content: The string returned by the LLM

    Returns:
        Cleaned string with all code block markers removed
    """
    # Remove all lines that start with ```
    return re.sub(r"^```[^\n]*\n|^```$", "", content, flags=re.MULTILINE).strip()


async def get_api_key() -> str:
    """
    Get OpenAI API Key with fallback mechanisms
    1. Try environment variable
    2. Try global state
    3. Prompt user to enter key if not found

    Returns:
        API Key string

    Raises:
        Error: If API key not found
    """
    # First try environment variable
    env_api_key = os.getenv("OPENAI_API_KEY")
    if env_api_key:
        print("Using environment variable for OpenAI API Key")
        return env_api_key
    # Fallback - you can implement additional logic here
    raise ValueError("OpenAI API key not found")


async def call_llm(prompt: str, parse_json: bool = False) -> Any:
    """
    Common function to call LLM API

    Args:
        prompt: The prompt to send to LLM
        parse_json: Whether to parse the response as JSON

    Returns:
        The LLM response

    Raises:
        Error: If API key not found or API call fails
    """
    api_key = await get_api_key()
    if not api_key:
        raise ValueError(
            "OpenAI API key not found. Please set it in environment variables or enter it when prompted."
        )

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful programming assistant.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        content = response.choices[0].message.content or ""

        if parse_json:
            cleaned = clean_llm_code_block(content)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Failed to parse LLM response as JSON: {cleaned}"
                ) from e
        return content

    except Exception as e:
        raise ValueError(f"OpenAI API error: {str(e)}") from e


async def get_code_summary(code: str, file_context: str) -> Dict[str, str]:
    """
    Get a multi-level summary of the given code using LLM

    Args:
        code: The code to summarize
        file_context: The file context where the code is located

    Returns:
        Object containing title, concise, detailed, and bulleted summaries
    """
    prompt = f"""
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

File Context (for reference only):
{file_context}

Code to summarize:
{code}
"""

    parsed = await call_llm(prompt, True)
    result = {
        "title": parsed.get("title", ""),
        "low_unstructured": parsed.get("low_unstructured", ""),
        "low_structured": parsed.get("low_structured", ""),
        "medium_unstructured": parsed.get("medium_unstructured", ""),
        "medium_structured": parsed.get("medium_structured", ""),
        "high_unstructured": parsed.get("high_unstructured", ""),
        "high_structured": parsed.get("high_structured", ""),
    }
    return result


async def get_summary_with_reference(
    new_code: str, original_code: str, old_summary: Dict[str, str], file_context: str
) -> Dict[str, str]:
    """
    Get a multi-level summary of modified code, referencing the original code and old summary.
    The new summary should be as close as possible to the old summary, only updating parts affected by the code change.

    Args:
        new_code: The modified code
        original_code: The original code before modification
        old_summary: The old summary object: { title, concise, detailed, bullets }
        file_context: The file context where the code is located

    Returns:
        Object containing title, concise, detailed, and bulleted summaries
    """
    prompt = f"""
You are an expert code summarizer. Your task is to generate a new summary for the MODIFIED code below, using the original code and its previous summary as reference.

Instructions:
- Your new summary MUST focus on the code differences (addition, deletion) between the original and modified code and clearly reflect those changes, even if they are small, such as inline comments.
- Make the changed parts of the summary easy to identify (e.g., by being explicit about what changed, or by using wording that highlights the update). I mean, rather than describing the change itself (e.g., updated the function to ...), seamlessly integrate the changes into the new summary in one coherent, descriptive sentence.
- The new summary should be close to the old summary, only updating the parts that are affected by the code change:  If a part of the summary is still accurate for the new code, keep it unchanged; If a part of the summary is no longer accurate, change only that part to reflect the new code. Do not add unnecessary changes or rephrase unchanged parts.
- For all structured (bulleted) summaries, return as a single string. Each bullet must start with "•" and be separated by \\n. For medium_structured and high_structured, if there are logical groupings, you should use two-level bullets ("•" and "◦"). For the second-level bullet ("◦"), always indent with 2 spaces before the "◦". Never return an array.
- Return your response as a JSON object with keys: title, low_unstructured, low_structured, medium_unstructured, medium_structured, high_unstructured, high_structured.

File Context (for reference only):
{file_context}

Original code:
{original_code}

Old summary:
{{
  "title": "{old_summary['title']}",
  "low_unstructured": "{old_summary['low_unstructured']}",
  "low_structured": "{old_summary['low_structured']}",
  "medium_unstructured": "{old_summary['medium_unstructured']}",
  "medium_structured": "{old_summary['medium_structured']}",
  "high_unstructured": "{old_summary['high_unstructured']}",
  "high_structured": "{old_summary['high_structured']}"
}}

MODIFIED code:
{new_code}
"""

    parsed = await call_llm(prompt, True)
    result = {
        "title": parsed.get("title", ""),
        "low_unstructured": parsed.get("low_unstructured", ""),
        "low_structured": parsed.get("low_structured", ""),
        "medium_unstructured": parsed.get("medium_unstructured", ""),
        "medium_structured": parsed.get("medium_structured", ""),
        "high_unstructured": parsed.get("high_unstructured", ""),
        "high_structured": parsed.get("high_structured", ""),
    }
    return result


async def build_summary_mapping(
    code: str, summary_text: str, real_start_line: int = 1
) -> List[Dict[str, Any]]:
    """
    Build summary-to-code mapping for a given summary and code using LLM.
    Supports multiple, possibly non-contiguous code ranges per summary component.

    Args:
        code: The code to map
        summary_text: The summary text (concise, detailed, or a bullet)
        real_start_line: The real starting line number for the code

    Returns:
        List of mapping objects with summaryComponent and codeSegments
    """
    code_with_line_numbers = "\n".join(
        f"{idx + real_start_line}: {line}" for idx, line in enumerate(code.split("\n"))
    )

    prompt = f"""
You are an expert at code-to-summary mapping. Given the following code and summary, extract up to 10 key summary components (phrases or semantic units) from the summary.

IMPORTANT:
1. Each summaryComponent you extract MUST be a substring (exact part) of the summary text below.
2. Extract summaryComponents in the exact order they appear in the summary text.
3. Do NOT hallucinate or invent summary components that do not appear in the summary.

For each summaryComponent, extract one or more relevant code segments from the code that best match the meaning of the summary component.
- For each code segment, return both the code fragment (as a string) and its line number in the original code (1-based).
- Prefer to use a complete code statement (such as a full line, assignment, function definition, or block) as the code segment if it clearly represents the summary component's meaning.
- If a full statement is not appropriate or would be ambiguous, you should use a smaller, relevant fragment (such as a variable, function name, operator, or part of an expression).
- Only include enough code to make the mapping meaningful and unambiguous.
- If a code segment contains multiple lines, split them into separate objects in the codeSegments array.

Return as a JSON array of objects:
[
  {{ 
    "summaryComponent": "...", 
    "codeSegments": [
      {{ "code": "code fragment 1", "line": 12 }},
      {{ "code": "code fragment 2", "line": 15 }}
    ]
  }},
  ...
]

Code (with line numbers for reference):
{code_with_line_numbers}

Summary:
{summary_text}
"""

    raw = await call_llm(prompt, False)
    parsed = None

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        cleaned = clean_llm_code_block(raw)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {cleaned}") from e

    if isinstance(parsed, list):
        filtered = []
        for item in parsed:
            if (
                isinstance(item.get("summaryComponent"), str)
                and item["summaryComponent"] not in summary_text
            ):
                print(
                    f"[build_summary_mapping] summaryComponent not found in summary: {item['summaryComponent']}"
                )
                continue

            if not isinstance(item.get("codeSegments"), list):
                item["codeSegments"] = []
            filtered.append(item)

        return filtered

    return []
