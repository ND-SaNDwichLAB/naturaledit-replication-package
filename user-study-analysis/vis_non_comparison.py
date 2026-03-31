import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Read the data from the file
data = pd.read_csv("questionnaires/post_study.txt", sep="\t")

# Extract participant IDs and remove them from the data
participant_ids = data["ID"]
data_numeric = data.drop("ID", axis=1)

# Define the non-comparison questions (NaturalEdit-specific)
non_comparison_questions = [
    "The adaptive and multifaceted summaries helped in understanding the code at different levels",
    "The interactive mapping between summary and code made their relationship explicit and easy to follow",
    "By applying direct instructions to the summary, I was able to express my intentions flexibly and efficiently",
    "The auto-updated summary with visual diffs helped me validate the changes in a consistent workflow",
]

# Short labels for visualization
short_labels = [
    "$\mathbf{Abstraction\ Gradient:}$ Adaptive Representation Aids Code Comprehension",
    "$\mathbf{Closeness\ of\ Mapping:}$ Interactive Mapping Clarifies NL-Code Relationship",
    "$\mathbf{Viscosity:}$ Intent-Driven Workflow Streamlines Intent Expression",
    "$\mathbf{Visibility\ &\ Consistency:}$ Bidirectional Sync & Diffs Support Change Validation",
]

# Extract NaturalEdit-specific data (last 4 columns)
naturaledit_specific_data = data_numeric.iloc[:, -4:]

# Transpose the data so questions become rows and participants become columns
naturaledit_specific_data = naturaledit_specific_data.T

# Set the index names
naturaledit_specific_data.index = short_labels

# Total responses
TOTAL_SAMPLES = len(participant_ids)

# Process NaturalEdit-specific data
df_count_naturaledit = pd.DataFrame(index=naturaledit_specific_data.index)
for i in range(1, 8):
    df_count_naturaledit[i] = (naturaledit_specific_data == i).sum(axis=1)
df_count_naturaledit = df_count_naturaledit[::-1]

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

fig, ax = plt.subplots(1, 1, figsize=(10, 1.7))

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
    # ax.set_title(title, fontsize=15, fontweight="semibold", pad=0)
    ax.set_xlabel("")
    ax.set_xticks([])

    # Set y-axis labels
    ax.set_yticks(range(len(index_labels)), labels=index_labels)
    ax.tick_params(axis="y", length=0, labelsize=11)
    ax.yaxis.set_tick_params(pad=5)

    # Remove spines
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Draw center line at the shifted center position
    ax.axvline(center_shift, color="gray", linewidth=1, linestyle="--")


# Create the plot
plot_diverging(
    ax,
    naturaledit_left,
    naturaledit_neutral,
    naturaledit_right,
    "NaturalEdit-Specific Questions",
    df_count_naturaledit.index,
)

# Set x-axis limits
max_left_width = naturaledit_left.sum(axis=1).max() if not naturaledit_left.empty else 0
max_right_width = (
    naturaledit_right.sum(axis=1).max() if not naturaledit_right.empty else 0
)
max_neutral_width = naturaledit_neutral.max() if not naturaledit_neutral.empty else 0

left_margin = max_left_width + TOTAL_SAMPLES * 0.1
right_margin = max_right_width + TOTAL_SAMPLES * 0.1

ax.set_xlim(-left_margin, right_margin)

# Add legend on the right side
handles = [plt.Rectangle((0, 0), 1, 1, color=color_map[str(i)]) for i in range(1, 8)]
fig.legend(
    handles,
    likert_labels,
    loc="center right",
    bbox_to_anchor=(1.21, 0.5),
    fontsize=11,
)

plt.tight_layout(pad=0)
fig.savefig("figures/likert_non_comparison.pdf", bbox_inches="tight", dpi=300)
plt.show()
