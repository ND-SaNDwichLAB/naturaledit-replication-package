import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def load_statistics(csv_path: str) -> pd.DataFrame:
    """Load the final statistics CSV into a DataFrame."""
    return pd.read_csv(csv_path)


def extract_series(df: pd.DataFrame, metric_name: str, prefix: str) -> tuple:
    """Extract means and SDs for Low/Medium/High for a given metric and prefix.

    Returns (means, sds) as length-3 lists.
    """
    row = df[df["Metric"] == metric_name]
    if row.empty:
        raise ValueError(f"Metric '{metric_name}' not found in CSV.")
    row = row.iloc[0]
    means = [
        row[f"{prefix}-Low-M"],
        row[f"{prefix}-Medium-M"],
        row[f"{prefix}-High-M"],
    ]
    sds = [
        row[f"{prefix}-Low-SD"],
        row[f"{prefix}-Medium-SD"],
        row[f"{prefix}-High-SD"],
    ]
    return means, sds


def plot_category_row(ax_row, df: pd.DataFrame, metrics: list, titles: list):
    """Plot a row of subplots for the given metrics.

    ax_row: sequence of Axes objects for the row
    metrics: list of metric names to plot (length <= len(ax_row))
    titles: titles per subplot (same length as metrics)
    """
    x_positions = np.arange(3)
    x_labels = ["Low", "Medium", "High"]

    for idx, metric in enumerate(metrics):
        ax = ax_row[idx]

        un_m, un_sd = extract_series(df, metric, "Unstructured")
        st_m, st_sd = extract_series(df, metric, "Structured")

        un_m = np.array(un_m, dtype=float)
        un_sd = np.array(un_sd, dtype=float)
        st_m = np.array(st_m, dtype=float)
        st_sd = np.array(st_sd, dtype=float)

        # SD shaded bands
        ax.fill_between(
            x_positions,
            un_m - un_sd,
            un_m + un_sd,
            color="#1f77b4",
            alpha=0.15,
            linewidth=0,
        )
        ax.fill_between(
            x_positions,
            st_m - st_sd,
            st_m + st_sd,
            color="#ff7f0e",
            alpha=0.15,
            linewidth=0,
        )

        # Mean lines
        ax.plot(
            x_positions,
            un_m,
            marker="o",
            label="Unstructured",
            color="#1f77b4",
            alpha=0.8,
        )
        ax.plot(
            x_positions,
            st_m,
            marker="o",
            label="Structured",
            color="#ff7f0e",
            alpha=0.8,
        )
        ax.set_title(titles[idx], fontsize=13)
        ax.set_ylim(2.5, 5.5)
        ax.set_yticks([3, 4, 5])
        ax.set_xticks(x_positions, x_labels)
        ax.set_xlim(-0.2, 2.2)
        ax.tick_params(axis="both", which="both", labelsize=12, length=0, width=0)
        ax.grid(True, linestyle=":", linewidth=0.8, alpha=0.6)
        # Add y-axis label only for the leftmost subplot in the row
        if idx == 0:
            ax.set_ylabel("Rating (1–5)", fontsize=12)

    # Hide unused axes in the row, if any
    for j in range(len(metrics), len(ax_row)):
        ax_row[j].axis("off")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "data", "final_statistics.csv")
    out_path = os.path.join(script_dir, "final_statistics_plots.pdf")

    df = load_statistics(csv_path)

    # Define metric groups
    summary_metrics = [
        "Summary Accuracy",
        "Summary Clarity",
    ]
    mapping_metrics = [
        "Segmentation Granularity",
        "Mapping Accuracy",
        "Mapping Coverage",
    ]
    diff_metrics = [
        "Diff Faithfulness",
        "Diff Completeness",
        "Diff Salience",
    ]

    # Prepare figure: 3 rows x 3 columns (unused axes will be hidden for row 1)
    fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(8, 5), constrained_layout=True)

    # Row 1: Summary quality
    plot_category_row(
        axes[0],
        df,
        metrics=summary_metrics,
        titles=["Summary Accuracy", "Summary Clarity"],
    )

    # Row 2: Mapping quality (including segmentation)
    plot_category_row(
        axes[1],
        df,
        metrics=mapping_metrics,
        titles=["Segmentation Granularity", "Mapping Accuracy", "Mapping Coverage"],
    )

    # Row 3: Diff quality
    plot_category_row(
        axes[2],
        df,
        metrics=diff_metrics,
        titles=["Diff Faithfulness", "Diff Completeness", "Diff Salience"],
    )

    # Add a single legend for the whole figure (from the first subplot)
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper right",
        bbox_to_anchor=(0.98, 0.98),
        borderaxespad=0.8,
        ncol=1,
        fontsize=12,
    )

    fig.savefig(out_path, format="pdf")
    print(f"Saved figure to: {out_path}")


if __name__ == "__main__":
    main()
