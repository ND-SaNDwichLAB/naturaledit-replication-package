import pandas as pd
from scipy.stats import wilcoxon

# Read the data from the file
data = pd.read_csv("questionnaires/post_study.txt", sep="\t")

# Extract participant IDs and remove them from the data
participant_ids = data["ID"]
data_numeric = data.drop("ID", axis=1)

# Define the comparison questions (NaturalEdit vs PASTA)
comparison_questions = [
    "This system's capabilities meet my requirements",
    "This system is easy to use",
    "I can quickly learn how to use the system",
    "I would use this system in my real development work if it were available",
    "The system helps me comprehend the original code",
    "The system supports me in specifying my intentions",
    "The system helps me understand and validate the modified code",
    "The system assists with the iterative refinement of code",
    "The natural language representation is useful for achieving the task goal",
    "I felt a good sense of control over the system's behavior",
    "I am generally satisfied with the code modifications produced by the system",
]

# Extract NaturalEdit data (columns 1-12, 0-indexed) - first 11 comparison questions
naturaledit_data = data_numeric.iloc[:, 1:12]

# Extract PASTA data (columns 12-23, 0-indexed) - corresponding PASTA questions
pasta_data = data_numeric.iloc[:, 12:23]

# Transpose the data so questions become rows and participants become columns
naturaledit_data = naturaledit_data.T
pasta_data = pasta_data.T

# Set the index names for both dataframes
naturaledit_data.index = comparison_questions
pasta_data.index = comparison_questions


# --- SUS Score Calculation for UMUX-Lite Items (first two questions) ---
def calc_sus_score(item1, item2):
    sus_scores = 0.65 * ((item1 + item2 - 2) * (100 / 12)) + 22.9
    return sus_scores


# Get UMUX-Lite items (first two questions)
umux_naturaledit = naturaledit_data.iloc[0:2, :]
umux_pasta = pasta_data.iloc[0:2, :]

sus_naturaledit = calc_sus_score(umux_naturaledit.iloc[0], umux_naturaledit.iloc[1])
sus_pasta = calc_sus_score(umux_pasta.iloc[0], umux_pasta.iloc[1])

print(
    "\nSUS Score (NaturalEdit): Mean = {:.2f}, Std = {:.2f}, Median = {:.2f}".format(
        sus_naturaledit.mean(), sus_naturaledit.std(), sus_naturaledit.median()
    )
)
print(
    "SUS Score (PASTA): Mean = {:.2f}, Std = {:.2f}, Median = {:.2f}".format(
        sus_pasta.mean(), sus_pasta.std(), sus_pasta.median()
    )
)

# Wilcoxon signed-rank test for SUS scores
stat, p = wilcoxon(sus_naturaledit, sus_pasta)
print(f"Wilcoxon signed-rank test for SUS: statistic = {stat:.2f}, p-value = {p:.4f}\n")

# Perform Wilcoxon signed-rank test between NaturalEdit and PASTA
wilcoxon_results = {}
for question in comparison_questions:
    # Get the data for this question (participants as columns after transpose)
    ne_scores = naturaledit_data.loc[question].values
    pasta_scores = pasta_data.loc[question].values

    # Perform Wilcoxon test
    stat, p_value = wilcoxon(ne_scores, pasta_scores)

    # Calculate medians
    median_naturaledit = pd.Series(ne_scores).median()
    median_pasta = pd.Series(pasta_scores).median()

    wilcoxon_results[question] = {
        "statistic": stat,
        "p_value": round(p_value, 4),
        "median_naturaledit": median_naturaledit,
        "median_pasta": median_pasta,
    }

# Print the results in a formatted manner
print("Wilcoxon Signed-Rank Test Results (NaturalEdit vs PASTA):")
print("=" * 80)
for question, result in wilcoxon_results.items():
    print(f"{question}")
    print(
        f"  Mdn-NE: {result['median_naturaledit']}, Mdn-PASTA: {result['median_pasta']}, statistic: {result['statistic']:.2f}, p: {result['p_value']}"
    )

# Also print summary statistics
print("Summary Statistics:")
print("=" * 80)
print(f"Total participants: {len(participant_ids)}")
print(f"Total comparison questions: {len(comparison_questions)}")
print()

# Count significant results (p < 0.05)
significant_count = sum(
    1 for result in wilcoxon_results.values() if result["p_value"] < 0.05
)
print(
    f"Significant differences (p < 0.05): {significant_count}/{len(comparison_questions)}"
)

# Show which questions have significant differences
print("\nSignificant differences:")
for question, result in wilcoxon_results.items():
    if result["p_value"] < 0.05:
        direction = (
            "NaturalEdit > PASTA"
            if result["median_naturaledit"] > result["median_pasta"]
            else "PASTA > NaturalEdit"
        )
        print(
            f"  {question}: {direction} (statistic = {result['statistic']:.2f}, p = {result['p_value']})"
        )
