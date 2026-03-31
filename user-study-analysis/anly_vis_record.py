import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import wilcoxon

# Load data
df = pd.read_csv("./questionnaires/task_record.txt", sep="\t")

# Reshape FD and MP tasks into a single dataframe
fd = df[["ID", "FD-Condition", "FD-Time", "FD-A", "FD-B", "FD-C"]].rename(
    columns={
        "FD-Condition": "Condition",
        "FD-Time": "Time",
        "FD-A": "A",
        "FD-B": "B",
        "FD-C": "C",
    }
)
mp = df[["ID", "MP-Condition", "MP-Time", "MP-A", "MP-B", "MP-C"]].rename(
    columns={
        "MP-Condition": "Condition",
        "MP-Time": "Time",
        "MP-A": "A",
        "MP-B": "B",
        "MP-C": "C",
    }
)

df_all = pd.concat([fd, mp], ignore_index=True)

# Compute success flag (all subtasks correct)
df_all["Success"] = df_all[["A", "B", "C"]].sum(axis=1)

# Normalize condition labels (remove accidental leading/trailing spaces)
df_all["Condition"] = df_all["Condition"].astype(str).str.strip()

# ---- Plot (styled like study screenshot) ----
plt.figure(figsize=(5, 1.3))

# Determine condition order
conditions_order = ["NaturalEdit", "Baseline"]

# Default colors from matplotlib cycle: blue then orange
cycle_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
colors = [cycle_colors[0], cycle_colors[1] if len(cycle_colors) > 1 else "orange"]

# Scatter points per condition with transparency
for idx, cond in enumerate(conditions_order):
    print(idx, cond)
    times = df_all.loc[df_all["Condition"] == cond, "Time"]
    y_vals = [idx] * len(times)
    plt.scatter(
        times,
        y_vals,
        color=colors[idx % len(colors)],
        alpha=0.5,
        s=40,
        zorder=2,
    )

# Mean and std per condition with horizontal error bars and black diamond marker
stats = (
    df_all.groupby("Condition")["Time"].agg(["mean", "std"]).reindex(conditions_order)
)
for idx, (cond, row) in enumerate(stats.iterrows()):
    mean_v = row["mean"]
    std_v = row["std"] if pd.notnull(row["std"]) else 0.0
    plt.errorbar(
        x=mean_v,
        y=idx,
        xerr=std_v,
        fmt="D",
        color="black",
        ecolor="black",
        elinewidth=1.0,
        capsize=0,
        markersize=6,
        zorder=3,
    )

# Aesthetics: remove frame, very light x-grid, set y labels
ax = plt.gca()
for spine in ["top", "right", "left", "bottom"]:
    ax.spines[spine].set_visible(False)
ax.grid(True, axis="x", color="#e6e6e6", linewidth=1.0)
ax.grid(True, axis="y", color="#e6e6e6", linewidth=1.0)
ax.set_yticks(list(range(len(conditions_order))))
ax.set_yticklabels(conditions_order)
plt.xlabel("Time (minutes)")
plt.ylabel("")
plt.xlim(7, 26)
plt.ylim(-0.4, 1.4)
plt.tight_layout(pad=0)
plt.savefig("figures/time_record.pdf", bbox_inches="tight")
plt.show()

# ---- Print statistics ----
summary = df_all.groupby("Condition").agg(
    mean_time=("Time", "mean"),
    std_time=("Time", "std"),
    success_rate=("Success", "mean"),
)

# Convert success_rate to percentage
summary["success_rate"] = summary["success_rate"] / 3 * 100

print("=== Summary by System ===")
for cond, row in summary.iterrows():
    print(
        f"{cond}: {row['mean_time']:.2f} ± {row['std_time']:.2f} minutes, "
        f"Success Rate = {row['success_rate']:.1f}%"
    )

# ---- Wilcoxon signed-rank tests on Time (paired by participant) ----
# Overall (average across tasks per participant per condition)
overall_times = (
    df_all.groupby(["ID", "Condition"])["Time"]  # participant-condition
    .mean()  # average across FD/MP if both exist
    .reset_index()
    .pivot(index="ID", columns="Condition", values="Time")
)

if overall_times.shape[1] == 2:
    cond_names = list(overall_times.columns)
    paired = overall_times.dropna()
    if len(paired) > 0:
        stat_overall, p_overall = wilcoxon(paired[cond_names[0]], paired[cond_names[1]])
        print(
            f"\n=== Wilcoxon Signed-Rank (Overall, mean per ID) ===\n"
            f"{cond_names[0]} vs {cond_names[1]}: statistic={stat_overall:.3f}, p={p_overall:.4f}"
        )

# Per task: FD
fd_times = (
    fd.groupby(["ID", "Condition"])["Time"]
    .mean()
    .reset_index()
    .pivot(index="ID", columns="Condition", values="Time")
)
if fd_times.shape[1] == 2:
    cond_names_fd = list(fd_times.columns)
    paired_fd = fd_times.dropna()
    if len(paired_fd) > 0:
        stat_fd, p_fd = wilcoxon(
            paired_fd[cond_names_fd[0]], paired_fd[cond_names_fd[1]]
        )
        print(
            f"\n=== Wilcoxon Signed-Rank (FD) ===\n"
            f"{cond_names_fd[0]} vs {cond_names_fd[1]}: statistic={stat_fd:.3f}, p={p_fd:.4f}"
        )

# Per task: MP
mp_times = (
    mp.groupby(["ID", "Condition"])["Time"]
    .mean()
    .reset_index()
    .pivot(index="ID", columns="Condition", values="Time")
)
if mp_times.shape[1] == 2:
    cond_names_mp = list(mp_times.columns)
    paired_mp = mp_times.dropna()
    if len(paired_mp) > 0:
        stat_mp, p_mp = wilcoxon(
            paired_mp[cond_names_mp[0]], paired_mp[cond_names_mp[1]]
        )
        print(
            f"\n=== Wilcoxon Signed-Rank (MP) ===\n"
            f"{cond_names_mp[0]} vs {cond_names_mp[1]}: statistic={stat_mp:.3f}, p={p_mp:.4f}"
        )
