import pandas as pd
import numpy as np

# Read the data from the file
data = pd.read_csv("questionnaires/post_study.txt", sep="\t")

# Extract participant IDs and remove them from the data
participant_ids = data["ID"]
data_numeric = data.drop("ID", axis=1)

# Define the questions to analyze
questions_to_analyze = {
    "realistic": "The study tasks felt as realistic as my daily programming.",
    "adaptive_summaries": "The adaptive and multifaceted summaries helped in understanding the code at different levels",
    "interactive_mapping": "The interactive mapping between summary and code made their relationship explicit and easy to follow",
    "direct_instructions": "By applying direct instructions to the summary, I was able to express my intentions flexibly and efficiently",
    "auto_updated_diffs": "The auto-updated summary with visual diffs helped me validate the changes in a consistent workflow",
}

# Get the column indices for these questions
realistic_col = 0  # First column (0-indexed)
naturaledit_specific_cols = [-4, -3, -2, -1]  # Last 4 columns

# Analyze each question
print("Analysis of Questionnaire Responses")
print("=" * 50)
print()

for i, (question_key, question_text) in enumerate(questions_to_analyze.items()):
    print(f"Question {i+1}: {question_text}")
    print("-" * 80)

    if question_key == "realistic":
        # First question (realistic)
        responses = data_numeric.iloc[:, realistic_col]
        col_name = data_numeric.columns[realistic_col]
    else:
        # NaturalEdit-specific questions (last 4 columns)
        col_idx = naturaledit_specific_cols[
            list(questions_to_analyze.keys()).index(question_key) - 1
        ]
        responses = data_numeric.iloc[:, col_idx]
        col_name = data_numeric.columns[col_idx]

    print(f"Column: {col_name}")
    print(f"Total responses: {len(responses)}")
    print()

    # Count each score value
    print("Score distribution:")
    for score in range(1, 8):
        count = (responses == score).sum()
        percentage = (count / len(responses)) * 100
        print(f"  Score {score}: {count} responses ({percentage:.1f}%)")

    # Calculate median
    median = responses.median()
    print(f"\nMedian: {median}")

    # Additional statistics
    mean = responses.mean()
    std = responses.std()
    print(f"Mean: {mean:.2f}")
    print(f"Standard deviation: {std:.2f}")

    print("\n" + "=" * 50 + "\n")

# Summary table
print("Summary Table")
print("=" * 50)
print(f"{'Question':<50} {'Median':<8} {'Mean':<8} {'Std':<8}")
print("-" * 50)

for question_key, question_text in questions_to_analyze.items():
    if question_key == "realistic":
        responses = data_numeric.iloc[:, realistic_col]
    else:
        col_idx = naturaledit_specific_cols[
            list(questions_to_analyze.keys()).index(question_key) - 1
        ]
        responses = data_numeric.iloc[:, col_idx]

    median = responses.median()
    mean = responses.mean()
    std = responses.std()

    # Truncate question text for display
    short_text = (
        question_text[:47] + "..." if len(question_text) > 50 else question_text
    )
    print(f"{short_text:<50} {median:<8.1f} {mean:<8.2f} {std:<8.2f}")
