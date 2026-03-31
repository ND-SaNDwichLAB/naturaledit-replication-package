import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Read the data from the file
data = pd.read_csv("questionnaires/post_study.txt", sep="\t")

# Extract participant IDs and remove them from the data
participant_ids = data["ID"]
data_numeric = data.drop("ID", axis=1)

# Define the comparison questions (NaturalEdit vs PASTA) with short labels for visualization
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

# Short labels for visualization
short_labels = [
    "Q1: Meets Requirements",
    "Q2: Ease of System Use",
    "Q3: Quick to Learn",
    "Q4: Usefulness in Real Work",
    "Q5: Helps Comprehend Code",
    "Q6: Supports Specifying Intent",
    "Q7: Helps Validate Edits",
    "Q8: Assists Iterative Refinement",
    "Q9: Utility of NL Representation",
    "Q10: Provides Sense of Control",
    "Q11: Satisfaction with Edits",
]

# Extract NaturalEdit data (columns 1-12, 0-indexed) - first 11 comparison questions
naturaledit_data = data_numeric.iloc[:, 1:12]

# Extract PASTA data (columns 12-23, 0-indexed) - corresponding PASTA questions
pasta_data = data_numeric.iloc[:, 12:23]

# Transpose the data so questions become rows and participants become columns
naturaledit_data = naturaledit_data.T
pasta_data = pasta_data.T

# Set the index names for both dataframes
naturaledit_data.index = short_labels
pasta_data.index = short_labels

# Define which questions are significant (based on your requirement: 2 and 3 are NOT significant)
significant_questions = [
    True,
    True,
    True,
    True,
    True,
    True,
    True,
    True,
    False,
    False,
    True,
]

# Total responses
TOTAL_SAMPLES = len(participant_ids)

# Process NaturalEdit
df_count_naturaledit = pd.DataFrame(index=naturaledit_data.index)
for i in range(1, 8):
    df_count_naturaledit[i] = (naturaledit_data == i).sum(axis=1)
df_count_naturaledit = df_count_naturaledit[::-1]

# Process PASTA
df_count_pasta = pd.DataFrame(index=pasta_data.index)
for i in range(1, 8):
    df_count_pasta[i] = (pasta_data == i).sum(axis=1)
df_count_pasta.columns = [str(i) for i in range(1, 8)]
df_count_pasta = df_count_pasta[::-1]

# Likert labels and colors
likert_labels = [
    "1 - Strongly Disagree",
    "2",
    "3",
    "4 - Neutral",
    "5",
    "6",
    "7 - Strongly Agree",
]
colors = sns.color_palette("RdBu", 7).as_hex()
color_map = {
    "1": colors[0],
    "2": colors[1],
    "3": colors[2],
    "4": colors[3],  # Neutral
    "5": colors[4],
    "6": colors[5],
    "7": colors[6],
}


# Prepare diverging data
def prepare_diverging(df):
    left = df.iloc[:, :3]  # 1-3
    neutral = df.iloc[:, 3]  # 4
    right = df.iloc[:, 4:]  # 5-7
    return left, neutral, right


naturaledit_left, naturaledit_neutral, naturaledit_right = prepare_diverging(
    df_count_naturaledit
)
pasta_left, pasta_neutral, pasta_right = prepare_diverging(df_count_pasta)

fig, axes = plt.subplots(
    1, 2, figsize=(15, 4.5), sharey=True, gridspec_kw={"wspace": 0}
)

bar_width = 0.9


def plot_diverging(ax, left, neutral, right, title, index_labels, center_shift=0):
    y_pos = range(len(left))

    # Draw neutral bars (gray tone) first to get center position
    neutral_width = neutral
    neutral_start = -neutral_width / 2 + center_shift
    ax.barh(
        y_pos,
        neutral_width,
        left=neutral_start,
        color=color_map["4"],
        edgecolor="white",
        height=bar_width,
        alpha=0.8,
    )

    # Draw left (negative) bars
    left_cumsum = left.cumsum(axis=1)
    left_sum = left.sum(axis=1)
    for col in left.columns:
        widths = left[col]
        starts = neutral_start - left_sum + left_cumsum[col] - widths
        ax.barh(
            y_pos,
            widths,
            left=starts,
            color=color_map[str(int(col))],
            edgecolor="white",
            height=bar_width,
            alpha=0.8,
        )

    # Draw right (positive) bars
    right_cumsum = right.cumsum(axis=1)
    for i, col in enumerate(right.columns):
        widths = right[col]
        starts = neutral_start + neutral_width + right_cumsum[col] - widths
        ax.barh(
            y_pos,
            widths,
            left=starts,
            color=color_map[str(int(col))],
            edgecolor="white",
            height=bar_width,
            alpha=0.8,
        )

    # Add counts inside bars
    for i, (neg_row, neu_value, pos_row) in enumerate(
        zip(left.values, neutral.values, right.values)
    ):
        # === Left side ===
        # Calculate the starting position for left bars
        left_start = neutral_start.iloc[i] - left_sum.iloc[i]
        for j, count in enumerate(neg_row):
            if count > 0:
                # Position label at the center of each left bar
                bar_center = left_start + left_cumsum.iloc[i, j] - count / 2
                ax.text(
                    bar_center,
                    i,
                    str(int(count)),
                    va="center",
                    ha="center",
                    fontsize=10,
                    color="black",
                )

        # === Neutral ===
        if neu_value > 0:
            # Position label at the center of neutral bar
            neutral_center = neutral_start.iloc[i] + neu_value / 2
            ax.text(
                neutral_center,
                i,
                str(int(neu_value)),
                va="center",
                ha="center",
                fontsize=10,
                color="black",
            )

        # === Right side ===
        # Calculate the starting position for right bars
        right_start = neutral_start.iloc[i] + neu_value
        for j, count in enumerate(pos_row):
            if count > 0:
                # Position label at the center of each right bar
                bar_center = right_start + right_cumsum.iloc[i, j] - count / 2
                ax.text(
                    bar_center,
                    i,
                    str(int(count)),
                    va="center",
                    ha="center",
                    fontsize=10,
                    color="black",
                )

    # Settings
    ax.set_title(
        title, fontsize=15, fontweight="semibold", pad=0
    )  # Move title to the right
    ax.set_xlabel("")
    ax.set_xticks([])

    # Modify y-axis labels to append * and make significant ones bold
    modified_labels = []
    for i, label in enumerate(index_labels[::-1]):
        # Check if this question is significant (reverse the order since we're iterating backwards)
        original_index = len(index_labels) - 1 - i
        is_significant = significant_questions[original_index]

        if is_significant:
            modified_labels.append(
                r"$\mathbf{" + label.replace(" ", r"\ ") + "*" + "}$"
            )
        else:
            modified_labels.append(label)
    modified_labels = modified_labels[::-1]
    ax.set_yticks(range(len(modified_labels)), labels=modified_labels)
    ax.tick_params(axis="y", length=0, labelsize=11)
    ax.yaxis.set_tick_params(pad=10)

    # Remove spines
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Draw center line at the shifted center position
    ax.axvline(center_shift, color="gray", linewidth=1, linestyle="--")


# Create the plots
plot_diverging(
    axes[1],
    naturaledit_left,
    naturaledit_neutral,
    naturaledit_right,
    "NaturalEdit",
    df_count_naturaledit.index,
)
plot_diverging(
    axes[0],
    pasta_left,
    pasta_neutral,
    pasta_right,
    "Baseline",
    df_count_pasta.index,
)

# Set consistent x-axis limits for both plots to ensure proper scaling
# Calculate the maximum range needed across both datasets
max_left_width_naturaledit = (
    naturaledit_left.sum(axis=1).max() if not naturaledit_left.empty else 0
)
max_right_width_naturaledit = (
    naturaledit_right.sum(axis=1).max() if not naturaledit_right.empty else 0
)
max_neutral_width_naturaledit = (
    naturaledit_neutral.max() if not naturaledit_neutral.empty else 0
)

max_left_width_pasta = pasta_left.sum(axis=1).max() if not pasta_left.empty else 0
max_right_width_pasta = pasta_right.sum(axis=1).max() if not pasta_right.empty else 0
max_neutral_width_pasta = pasta_neutral.max() if not pasta_neutral.empty else 0

# Use the maximum values from both datasets
max_left_width = max(max_left_width_naturaledit, max_left_width_pasta)
max_right_width = max(max_right_width_naturaledit, max_right_width_pasta)
max_neutral_width = max(max_neutral_width_naturaledit, max_neutral_width_pasta)

# Set consistent limits for both axes with some padding
left_margin = max_left_width + TOTAL_SAMPLES * 0.1
right_margin = max_right_width + TOTAL_SAMPLES * 0.1

axes[0].set_xlim(-left_margin, right_margin)
axes[1].set_xlim(-left_margin, right_margin)

# Add legend at the bottom with reduced spacing
handles = [plt.Rectangle((0, 0), 1, 1, color=color_map[str(i)]) for i in range(1, 8)]
fig.legend(
    handles,
    likert_labels,
    loc="lower center",
    ncol=7,
    bbox_to_anchor=(0.5, -0.08),
    fontsize=11,
)

plt.tight_layout(pad=0)  # Reduce padding for more compact layout
fig.savefig("figures/likert_naturaledit_vs_pasta.svg", bbox_inches="tight", dpi=300)
plt.show()
