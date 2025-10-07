#!/usr/bin/env python3
"""
Script to convert tasks.csv to JSON format.
This script reads the CSV file and converts it to a structured JSON format.
"""

import csv
import json
import os
from pathlib import Path


def csv_to_json(csv_file_path, json_file_path):
    """
    Convert CSV file to JSON format.

    Args:
        csv_file_path (str): Path to the input CSV file
        json_file_path (str): Path to the output JSON file
    """
    tasks = []

    try:
        with open(csv_file_path, "r", encoding="utf-8") as csvfile:
            # Create CSV reader with proper handling of quoted fields
            reader = csv.DictReader(csvfile)

            for row in reader:
                # Clean up the data by removing extra quotes and escaping
                cleaned_row = {}
                for key, value in row.items():
                    if value and value.startswith('"') and value.endswith('"'):
                        # Remove outer quotes and handle internal escaping
                        cleaned_value = value[1:-1].replace('""', '"')
                    else:
                        cleaned_value = value
                    cleaned_row[key] = cleaned_value

                tasks.append(cleaned_row)

        # Write to JSON file
        with open(json_file_path, "w", encoding="utf-8") as jsonfile:
            json.dump(tasks, jsonfile, indent=2, ensure_ascii=False)

        print(
            f"Successfully converted {len(tasks)} tasks from {csv_file_path} to {json_file_path}"
        )

    except FileNotFoundError:
        print(f"Error: File {csv_file_path} not found")
    except Exception as e:
        print(f"Error converting file: {e}")


def main():
    """Main function to run the conversion."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent

    # Define input and output file paths
    csv_file = script_dir / "data" / "tasks.csv"
    json_file = script_dir / "data" / "tasks.json"

    # Check if input file exists
    if not csv_file.exists():
        print(f"Error: Input file {csv_file} does not exist")
        return

    # Create output directory if it doesn't exist
    json_file.parent.mkdir(parents=True, exist_ok=True)

    # Convert CSV to JSON
    csv_to_json(str(csv_file), str(json_file))

    # Print some statistics
    if json_file.exists():
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"\nConversion completed successfully!")
            print(f"Total tasks converted: {len(data)}")
            print(f"Output file: {json_file}")

            # Show first few entries as preview
            if data:
                print(f"\nFirst task preview:")
                first_task = data[0]
                for key, value in first_task.items():
                    if key in ["old_code", "new_code", "old_context", "new_context"]:
                        # Truncate long code/context for display
                        preview = (
                            str(value)[:100] + "..."
                            if len(str(value)) > 100
                            else str(value)
                        )
                        print(f"  {key}: {preview}")
                    else:
                        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
