"""
Simple script to filter interactions by timestamp range.
Just modify the variables below and run the script.
"""

import json
from datetime import datetime
from pathlib import Path

# ===== CONFIGURATION =====
# Modify these variables as needed
INPUT_FILE = "naturaledit_interaction_2025_08_23.json"  # Change filename here
START_TIME = "2025-08-23 19:00:00"  # Change start time here
END_TIME = "2025-08-23 23:59:59"  # Change end time here
OUTPUT_FILE = None  # Leave as None for auto-generated filename, or specify custom name
# ========================


def parse_timestamp(timestamp_str):
    """Parse timestamp string to datetime object."""
    try:
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")


def main():
    # Parse timestamps
    start_dt = parse_timestamp(START_TIME)
    end_dt = parse_timestamp(END_TIME)

    print(f"Filtering interactions from {START_TIME} to {END_TIME}")
    print(f"Reading file: {INPUT_FILE}")

    # Get full path to input file
    input_path = Path(__file__).parent / "interactions" / INPUT_FILE

    if not input_path.exists():
        print(f"Error: File {input_path} not found")
        return

    try:
        # Read input file
        with open(input_path, "r", encoding="utf-8") as f:
            interactions = json.load(f)

        print(f"Total interactions in file: {len(interactions)}")

        # Filter interactions by timestamp
        filtered_interactions = []
        for interaction in interactions:
            if "timestamp" in interaction:
                try:
                    interaction_time = parse_timestamp(interaction["timestamp"])
                    if start_dt <= interaction_time <= end_dt:
                        filtered_interactions.append(interaction)
                except:
                    continue

        print(f"Filtered interactions: {len(filtered_interactions)}")

        # Generate output filename if not provided
        if OUTPUT_FILE is None:
            output_file = (
                input_path.parent
                / f"{input_path.stem}_filtered_{start_dt.strftime('%Y%m%d_%H%M')}_to_{end_dt.strftime('%Y%m%d_%H%M')}.json"
            )
        else:
            output_file = input_path.parent / OUTPUT_FILE

        # Write filtered interactions to output file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(filtered_interactions, f, indent=2, ensure_ascii=False)

        print(f"Filtered interactions saved to: {output_file}")

        # Print summary
        if filtered_interactions:
            first_time = parse_timestamp(filtered_interactions[0]["timestamp"])
            last_time = parse_timestamp(filtered_interactions[-1]["timestamp"])
            print(f"First interaction: {first_time}")
            print(f"Last interaction: {last_time}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
