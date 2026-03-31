import pandas as pd
from scipy.stats import wilcoxon

# Read the data from the file
data = pd.read_csv("questionnaires/post_task.txt", sep="\t")

# Extract participant IDs and remove them from the data
participant_ids = data["ID"]
data_numeric = data.drop(["ID", "Task"], axis=1)

# Define the comparison metrics (NASA-TLX and code understanding)
comparison_metrics = [
    "Mental Demand",
    "Physical Demand",
    "Temporal Demand",
    "Performance",
    "Effort",
    "Frustration",
    "Code Understanding",
    "Edits Understanding",
]

# Separate data by condition
naturaledit_data = data[data["Condition"] == "NaturalEdit"]
pasta_data = data[data["Condition"] == "PASTA"]

# Extract the comparison metrics for each condition
naturaledit_metrics = naturaledit_data[comparison_metrics]
pasta_metrics = pasta_data[comparison_metrics]

# Transpose the data so metrics become rows and participants become columns
naturaledit_metrics = naturaledit_metrics.T
pasta_metrics = pasta_metrics.T

# Set the index names for both dataframes
naturaledit_metrics.index = comparison_metrics
pasta_metrics.index = comparison_metrics

# Perform Wilcoxon signed-rank test between NaturalEdit and PASTA
wilcoxon_results = {}
for metric in comparison_metrics:
    # Get the data for this metric (participants as columns after transpose)
    ne_scores = naturaledit_metrics.loc[metric].values
    pasta_scores = pasta_metrics.loc[metric].values

    # Perform Wilcoxon test
    stat, p_value = wilcoxon(ne_scores, pasta_scores)

    # Calculate medians
    median_naturaledit = pd.Series(ne_scores).median()
    median_pasta = pd.Series(pasta_scores).median()

    wilcoxon_results[metric] = {
        "statistic": stat,
        "p_value": round(p_value, 4),
        "median_naturaledit": median_naturaledit,
        "median_pasta": median_pasta,
    }

# Print the results in a formatted manner
print("Wilcoxon Signed-Rank Test Results (NaturalEdit vs PASTA - Task Performance):")
print("=" * 80)
for metric, result in wilcoxon_results.items():
    print(f"{metric}")
    print(
        f"  Mdn-NE: {result['median_naturaledit']}, Mdn-PASTA: {result['median_pasta']}, statistic: {result['statistic']:.2f}, p: {result['p_value']}"
    )
print()

# Also print summary statistics
print("Summary Statistics:")
print("=" * 80)
print(f"Total participants: {len(participant_ids.unique())}")
print(f"Total tasks per participant: {len(data) // len(participant_ids.unique())}")
print(f"Total comparison metrics: {len(comparison_metrics)}")
print()

# Count significant results (p < 0.05)
significant_count = sum(
    1 for result in wilcoxon_results.values() if result["p_value"] < 0.05
)
print(
    f"Significant differences (p < 0.05): {significant_count}/{len(comparison_metrics)}"
)

# Show which metrics have significant differences
print("\nSignificant differences:")
for metric, result in wilcoxon_results.items():
    if result["p_value"] < 0.05:
        direction = (
            "NaturalEdit > PASTA"
            if result["median_naturaledit"] > result["median_pasta"]
            else "PASTA > NaturalEdit"
        )
        print(
            f"  {metric}: {direction} (statistic = {result['statistic']:.2f}, p = {result['p_value']})"
        )

# Additional analysis: Task-specific breakdown
print("\n" + "=" * 80)
print("Task-Specific Analysis:")
print("=" * 80)

# Analyze by task type
for task in ["JavaScript", "Python"]:
    print(f"\n{task} Tasks:")
    print("-" * 40)

    task_data = data[data["Task"] == task]
    task_naturaledit = task_data[task_data["Condition"] == "NaturalEdit"]
    task_pasta = task_data[task_data["Condition"] == "PASTA"]

    for metric in comparison_metrics:
        ne_scores = task_naturaledit[metric].values
        pasta_scores = task_pasta[metric].values

        if len(ne_scores) > 0 and len(pasta_scores) > 0:
            stat, p_value = wilcoxon(ne_scores, pasta_scores)
            median_ne = pd.Series(ne_scores).median()
            median_pasta = pd.Series(pasta_scores).median()

            print(
                f"  {metric}: Mdn-NE={median_ne}, Mdn-PASTA={median_pasta}, statistic={stat:.2f}, p={round(p_value, 4)}"
            )

# Summary by condition
print("\n" + "=" * 80)
print("Overall Summary by Condition:")
print("=" * 80)

print("\nNaturalEdit:")
for metric in comparison_metrics:
    scores = naturaledit_data[metric].values
    median_score = pd.Series(scores).median()
    mean_score = pd.Series(scores).mean()
    print(f"  {metric}: Mdn={median_score}, Mean={round(mean_score, 2)}")

print("\nPASTA:")
for metric in comparison_metrics:
    scores = pasta_data[metric].values
    median_score = pd.Series(scores).median()
    mean_score = pd.Series(scores).mean()
    print(f"  {metric}: Mdn={median_score}, Mean={round(mean_score, 2)}")
