import pandas as pd
from xgboost import XGBRanker
from sklearn.metrics import ndcg_score
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def load_data(path="data/merged_data.csv"):
    df = pd.read_csv(path)

    # Features to use
    feature_cols = [
        "PTS",
        "AST",
        "TRB",
        "FG%",
        "BPM",
        "WS/48",
        "TS%",
        "VORP",
        "WS",
        "PER",
    ]
    feature_cols = [
        col for col in feature_cols if col in df.columns
    ]  # only keep existing features
    df = df.dropna(subset=feature_cols + ["Rank"])

    # Sort by Year and Rank for consistency
    df = df.sort_values(by=["Year", "Rank"])

    X = df[feature_cols]
    y = df["Rank"]
    groups = df.groupby("Year").size().to_numpy()

    return X, y, groups, df


def evaluate_ndcg(y_true, y_pred, group_sizes):
    scores = []
    start = 0
    for size in group_sizes:
        true_ranks = y_true[start : start + size]
        true_relevance = (max(true_ranks) + 1) - true_ranks
        pred_scores = y_pred[start : start + size]
        scores.append(ndcg_score([true_relevance], [pred_scores]))
        start += size
    return np.mean(scores)


def plot_ranking_predictions(df, year):
    """
    Display real and predicted ranks side-by-side for comparison.

    Args:
        df: DataFrame containing prediction results
        year: Year to plot prediction errors for
    """
    year_df = df[df["Year"] == year].copy()
    year_df.sort_values("Rank", inplace=True)

    plt.figure(figsize=(12, 6))
    width = 0.35  # the width of the bars
    indices = np.arange(len(year_df))

    plt.bar(
        indices,
        year_df["Rank"],
        width,
        label="True Rank",
        color=sns.color_palette("coolwarm", 2)[0],
    )
    plt.bar(
        indices + width,
        year_df["PredictedRank"],
        width,
        label="Predicted Rank",
        color=sns.color_palette("coolwarm", 2)[1],
        alpha=0.6,
    )

    plt.xticks(indices + width / 2, year_df["Name"], rotation=45, ha="right")
    plt.ylabel("Rank")
    plt.title(f"MVP Ranking Predictions ({year})")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"data/ranking_predictions_{year}.png")


def main():
    X, y, group, df = load_data()

    # Train-test split on years
    unique_years = df["Year"].unique()
    train_years, test_years = (
        unique_years[:-2],  # train: 2018-2023
        unique_years[-2:],  # test: 2024-2025
    )

    train_idx = df["Year"].isin(train_years)
    test_idx = df["Year"].isin(test_years)

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # Group sizes
    train_groups = df[train_idx].groupby("Year").size().to_numpy()
    test_groups = df[test_idx].groupby("Year").size().to_numpy()

    # Model
    best_ndcg = -1
    best_n_estimators = 100
    for n_estimators in [100, 1000, 2000]:
        model = XGBRanker(
            objective="rank:pairwise",
            learning_rate=0.1,
            n_estimators=n_estimators,
            max_depth=4,
            random_state=42,
        )

        print(f"Training XGBoostRanker with {n_estimators} estimators...")
        model.fit(X_train, y_train, group=train_groups)

        # Predict and evaluate
        y_pred = model.predict(X_test)
        ndcg = evaluate_ndcg(y_test.to_numpy(), y_pred, test_groups)
        print(f"NDCG Score with {n_estimators} estimators: {ndcg:.4f}")

        if ndcg > best_ndcg:
            best_ndcg = ndcg
            best_n_estimators = n_estimators

    # Retrain with best n_estimators
    model = XGBRanker(
        objective="rank:pairwise",
        learning_rate=0.1,
        n_estimators=best_n_estimators,
        max_depth=4,
        random_state=42,
    )

    print(f"Retraining XGBoostRanker with best n_estimators: {best_n_estimators}")
    model.fit(X_train, y_train, group=train_groups)

    # Predict, sort, and evaluate
    y_pred = model.predict(X_test)
    df.loc[test_idx, "PredictedScore"] = y_pred
    df.loc[test_idx, "PredictedRank"] = (
        df.loc[test_idx]
        .groupby("Year")["PredictedScore"]
        .rank(ascending=False, method="first")
    )

    ndcg = evaluate_ndcg(y_test.to_numpy(), y_pred, test_groups)
    print(f"NDCG Score on test years {test_years.tolist()}: {ndcg:.4f}")

    # Show results
    print(df[test_idx][["Year", "Name", "Rank", "PredictedScore", "PredictedRank"]])
    plot_ranking_predictions(df, 2024)
    plot_ranking_predictions(df, 2025)


if __name__ == "__main__":
    main()
