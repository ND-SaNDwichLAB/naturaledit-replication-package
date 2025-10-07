import pandas as pd


def load_and_merge(mvp_path="data/mvp_votes.csv", stats_path="data/season_stats.csv"):
    mvp_df = pd.read_csv(mvp_path)
    stats_df = pd.read_csv(stats_path)

    # Normalize names
    mvp_df["Name"] = mvp_df["Name"].str.strip()
    stats_df["Player"] = stats_df["Player"].str.strip()

    # Merge on name + year
    merged = pd.merge(
        mvp_df,
        stats_df,
        left_on=["Name", "Year"],
        right_on=["Player", "Year"],
        how="left",
    )

    # Drop unnecessary columns
    drop_cols = ["Rk", "Player", "Pos", "Tm_y"]
    merged.drop(
        columns=[col for col in drop_cols if col in merged.columns], inplace=True
    )

    # Clean numeric columns
    for col in merged.columns:
        if merged[col].dtype == "object":
            try:
                merged[col] = merged[col].astype(float)
            except:
                pass

    # Assign ordinal MVP rank (1 = MVP)
    merged["Rank"] = merged.groupby("Year")["MVP_Points"].rank(
        ascending=False, method="first"
    )

    return merged


if __name__ == "__main__":
    df = load_and_merge()
    df.to_csv("data/merged_data.csv", index=False)
    print("Merged data saved to data/merged_data.csv")
