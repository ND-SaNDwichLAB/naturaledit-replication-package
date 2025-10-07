#!/usr/bin/env python3
"""
Simple script to count mappings for each task and summary level
"""

import json
from collections import defaultdict


def count_mappings():
    # Load the processed tasks data
    with open("output/processed_tasks.json", "r", encoding="utf-8") as f:
        tasks = json.load(f)

    # Initialize counters
    task_counts = defaultdict(lambda: defaultdict(int))

    # Count mappings for each task and summary level
    for task in tasks:
        task_id = task["task_id"]

        # Count old_code mappings
        if "old_code" in task and "mappings" in task["old_code"]:
            for level, mappings in task["old_code"]["mappings"].items():
                count = len(mappings)
                task_counts[task_id][f"old_{level}"] = count

        # Count new_code mappings
        if "new_code" in task and "mappings" in task["new_code"]:
            for level, mappings in task["new_code"]["mappings"].items():
                count = len(mappings)
                task_counts[task_id][f"new_{level}"] = count

    # Define the order for summary levels
    level_order = [
        "old_low_unstructured",
        "old_medium_unstructured",
        "old_high_unstructured",
        "old_low_structured",
        "old_medium_structured",
        "old_high_structured",
        "new_low_unstructured",
        "new_medium_unstructured",
        "new_high_unstructured",
        "new_low_structured",
        "new_medium_structured",
        "new_high_structured",
    ]

    # Print results
    print("Mapping counts by task:")
    print("=" * 50)
    for task_id in sorted(task_counts.keys()):
        print(f"\n{task_id}:")
        for level in level_order:
            if level in task_counts[task_id]:
                count = task_counts[task_id][level]
                print(f"  {level}: {count}")

    # Calculate max mappings for each summary level (without old/new prefix)
    print("\n" + "=" * 50)
    print("Maximum mappings for each summary level:")
    print("=" * 50)

    summary_levels = [
        "low_unstructured",
        "medium_unstructured",
        "high_unstructured",
        "low_structured",
        "medium_structured",
        "high_structured",
    ]

    for level in summary_levels:
        max_count = 0
        for task_id in task_counts:
            old_key = f"old_{level}"
            new_key = f"new_{level}"

            old_count = task_counts[task_id].get(old_key, 0)
            new_count = task_counts[task_id].get(new_key, 0)

            max_count = max(max_count, old_count, new_count)

        print(f"{level}: {max_count}")

    # Calculate total mappings
    print("\n" + "=" * 50)
    print("Total mappings:")
    print("=" * 50)

    total_mappings = 0
    for task_id in task_counts:
        for level in task_counts[task_id]:
            total_mappings += task_counts[task_id][level]

    print(f"Total mappings across all tasks: {total_mappings}")


if __name__ == "__main__":
    count_mappings()
