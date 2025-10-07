"""
Simple script to process code pairs from tasks.csv and generate summaries with mappings.
"""

import asyncio
import json
import os
import pandas as pd
from typing import Dict, Any
from llm_api import get_code_summary, get_summary_with_reference, build_summary_mapping


async def process_code_pair(
    old_code: str, new_code: str, file_context: str = "", task_id: str = ""
) -> Dict[str, Any]:
    """Process a pair of old and new code to generate summaries and mappings."""
    print(f"Processing task: {task_id}")

    try:
        # Get summary for old code
        print("Generating summary for old code...")
        old_summary = await get_code_summary(old_code, file_context)

        # Get summary for new code using reference
        print("Generating summary for new code with reference...")
        new_summary = await get_summary_with_reference(
            new_code, old_code, old_summary, file_context
        )

        # Build mappings for all summary levels
        summary_levels = [
            "low_unstructured",
            "low_structured",
            "medium_unstructured",
            "medium_structured",
            "high_unstructured",
            "high_structured",
        ]

        print("Building mappings for old code...")
        old_mappings = {}
        for level in summary_levels:
            if old_summary[level]:
                old_mappings[level] = await build_summary_mapping(
                    old_code, old_summary[level]
                )

        print("Building mappings for new code...")
        new_mappings = {}
        for level in summary_levels:
            if new_summary[level]:
                new_mappings[level] = await build_summary_mapping(
                    new_code, new_summary[level]
                )

        # Combine all data
        result = {
            "task_id": task_id,
            "metadata": {
                "file_context": file_context,
                "processing_timestamp": asyncio.get_event_loop().time(),
            },
            "old_code": {
                "code": old_code,
                "summary": old_summary,
                "mappings": old_mappings,
            },
            "new_code": {
                "code": new_code,
                "summary": new_summary,
                "mappings": new_mappings,
            },
        }

        return result

    except Exception as e:
        print(f"Error processing code pair: {str(e)}")
        return {
            "task_id": task_id,
            "error": str(e),
            "old_code": old_code,
            "new_code": new_code,
            "file_context": file_context,
        }


async def main():
    """Main function to process the tasks.csv file."""
    print("Code Summary Processing Script")
    print("=" * 40)

    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
        return

    # Process the tasks.csv file
    csv_file = "data/tasks.csv"
    output_file = "output/processed_tasks.json"

    if not os.path.exists(csv_file):
        print(f"Error: Input file not found: {csv_file}")
        return

    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)

    try:
        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} code pairs from {csv_file}")

        # Check required columns
        if "old_code" not in df.columns or "new_code" not in df.columns:
            raise ValueError("CSV must contain 'old_code' and 'new_code' columns")

        results = []

        for i, row in df.iterrows():
            print(f"\nProcessing pair {i+1}/{len(df)}")

            old_code = str(row["old_code"]).strip()
            new_code = str(row["new_code"]).strip()
            file_context = str(row.get("file_path", "")).strip()
            task_id = str(row.get("id", f"pair_{i+1}"))

            if not old_code or not new_code:
                print(f"Skipping pair {i+1}: Empty code")
                continue

            result = await process_code_pair(old_code, new_code, file_context, task_id)
            results.append(result)

            # Save intermediate results every 10 pairs
            if (i + 1) % 10 == 0:
                with open(f"{output_file}.temp", "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"Saved intermediate results")

        # Save final results
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\nResults saved to {output_file}")
        print(f"Total pairs processed: {len(results)}")

        successful = sum(1 for r in results if "error" not in r)
        errors = len(results) - successful
        print(f"Successful: {successful}, Errors: {errors}")

    except Exception as e:
        print(f"Error processing CSV file: {str(e)}")
        raise

    print("\nProcessing complete!")


if __name__ == "__main__":
    asyncio.run(main())
