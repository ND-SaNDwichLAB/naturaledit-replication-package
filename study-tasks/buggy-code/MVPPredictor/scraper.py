import pandas as pd
import os


def scrape_mvp_votes(start_year=2018, end_year=2025):
    all_votes = []
    for year in range(start_year, end_year + 1):
        url = f"https://www.basketball-reference.com/awards/awards_{year}.html"
        tables = pd.read_html(url, header=1)
        try:
            mvp_table = tables[0]  # MVP table is the first table
            mvp_table["Year"] = year
            all_votes.append(mvp_table)
        except:
            print(f"Could not parse year {year}")

    df = pd.concat(all_votes)
    df = df.rename(columns={"Player": "Name", "Pts Won": "MVP_Points"})
    return df[["Year", "Name", "MVP_Points"]]


def scrape_season_stats(year):
    base_url_reg = (
        f"https://www.basketball-reference.com/leagues/NBA_{year}_per_game.html"
    )
    df_reg = pd.read_html(base_url_reg, header=0)[0]
    df_reg = df_reg[df_reg["Player"] != "Player"]  # remove repeated header rows
    df_reg["Year"] = year

    df_reg = df_reg[
        ["Player", "Year", "PTS", "AST", "TRB", "FG%"]
    ]  # Keep only specified columns
    df_reg = df_reg.dropna(
        subset=["PTS", "AST", "TRB", "FG%"]
    )  # Ensure key stats aren't invalid
    return df_reg


def scrape_multiple_seasons(start_year=2018, end_year=2025):
    all_stats = []
    for year in range(start_year, end_year + 1):
        df = scrape_season_stats(year)
        all_stats.append(df)
    return pd.concat(all_stats)


if __name__ == "__main__":
    if not os.path.exists("data"):
        os.makedirs("data")

    print("Scraping MVP votes...")
    mvp_df = scrape_mvp_votes()
    mvp_df.to_csv("data/mvp_votes.csv", index=False)

    print("Scraping player stats...")
    stats_df = scrape_multiple_seasons()
    stats_df.to_csv("data/season_stats.csv", index=False)
