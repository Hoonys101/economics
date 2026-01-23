import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# 설정: DB 경로 및 그래프 저장 경로
DB_PATH = "simulation_data.db"
OUTPUT_DIR = "analysis_report"


def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def load_data(query, conn):
    try:
        return pd.read_sql_query(query, conn)
    except Exception as e:
        print(f"Error loading data with query '{query}': {e}")
        return pd.DataFrame()


def analyze_simulation():
    ensure_dir(OUTPUT_DIR)

    # 1. DB 연결
    if not os.path.exists(DB_PATH):
        print(f"[Error] DB file not found: {DB_PATH}")
        print("서버를 실행하여 시뮬레이션을 먼저 돌려주세요.")
        return

    conn = sqlite3.connect(DB_PATH)
    print(f"[Info] Connected to {DB_PATH}")

    # 2. 데이터 로드
    print("Loading Data...")

    # 2.1 Population & Avg Assets (Calculated from agent_states)
    # Note: DB uses 'time' column, we map it to 'tick' for consistency
    try:
        df_population = load_data(
            """
            SELECT time as tick, COUNT(*) as population 
            FROM agent_states 
            WHERE agent_type = 'household' AND is_active = 1 
            GROUP BY time
        """,
            conn,
        )

        df_assets = load_data(
            """
            SELECT time as tick, AVG(assets) as avg_household_assets
            FROM agent_states
            WHERE agent_type = 'household'
            GROUP BY time
        """,
            conn,
        )
    except Exception:
        print(
            "[Warning] Failed to query agent_states. Population/Asset charts may be incomplete."
        )
        df_population = pd.DataFrame()
        df_assets = pd.DataFrame()

    # 2.2 거시 경제 지표
    df_macro = load_data("SELECT * FROM economic_indicators ORDER BY time", conn)
    if not df_macro.empty:
        df_macro.rename(columns={"time": "tick"}, inplace=True)

    # 2.3 시장 가격 데이터
    df_market = load_data("SELECT * FROM market_history ORDER BY time", conn)
    if not df_market.empty:
        df_market.rename(columns={"time": "tick"}, inplace=True)

    conn.close()

    # Data Merging for Chart 1 & 2
    # We rely on 'df_macro' as the base, merging calculated metrics onto it
    if not df_macro.empty:
        if not df_population.empty:
            df_macro = pd.merge(df_macro, df_population, on="tick", how="left")
        if not df_assets.empty:
            df_macro = pd.merge(df_macro, df_assets, on="tick", how="left")
    else:
        # Fallback if economic_indicators is empty but we have agent data
        if not df_population.empty:
            df_macro = df_population
            if not df_assets.empty:
                df_macro = pd.merge(df_macro, df_assets, on="tick", how="left")
            # Add dummy unemployment if missing
            df_macro["unemployment_rate"] = 0

    if df_macro.empty:
        print(
            "[Warning] No macro data found (economic_indicators or agent_states missing)."
        )
        return

    # 3. 시각화 (Visualization)
    try:
        sns.set_theme(style="whitegrid")
    except:
        print(
            "[Info] Seaborn not found or failed to set theme, using default matplotlib style."
        )
        plt.style.use("ggplot")

    # --- Chart 1: The Great Filter (인구 & 실업률) ---
    print("Generating Chart 1: Population Survival...")
    fig, ax1 = plt.subplots(figsize=(12, 6))

    if "population" in df_macro.columns:
        sns.lineplot(
            data=df_macro,
            x="tick",
            y="population",
            ax=ax1,
            color="blue",
            label="Population",
            linewidth=2.5,
        )
        ax1.set_ylabel("Population", color="blue")
        # Set bottom to 0 to see scale correctly
        ax1.set_ylim(bottom=0)
    else:
        print("[Info] Population data missing, skipping population line.")

    if "unemployment_rate" in df_macro.columns:
        ax2 = ax1.twinx()
        sns.lineplot(
            data=df_macro,
            x="tick",
            y="unemployment_rate",
            ax=ax2,
            color="red",
            label="Unemployment Rate",
            linestyle="--",
        )
        ax2.set_ylabel("Unemployment Rate (%)", color="red")
        ax2.set_ylim(0, 105)

    plt.title("The Great Filter: Population vs Unemployment")
    output_path_1 = os.path.join(OUTPUT_DIR, "01_population_survival.png")
    plt.savefig(output_path_1)
    plt.close()
    print(f"[Saved] {output_path_1}")

    # --- Chart 2: Asset Meltdown (평균 자산 & 생산) ---
    print("Generating Chart 2: Economic Health...")
    # GDP 필드가 없으면 total_production 사용
    metric_col = "gdp" if "gdp" in df_macro.columns else "total_production"
    if metric_col not in df_macro.columns:
        metric_col = None

    fig, ax1 = plt.subplots(figsize=(12, 6))
    if "avg_household_assets" in df_macro.columns:
        sns.lineplot(
            data=df_macro,
            x="tick",
            y="avg_household_assets",
            ax=ax1,
            color="green",
            label="Avg Assets",
        )
        ax1.set_ylabel("Avg Assets", color="green")

    if metric_col:
        ax2 = ax1.twinx()
        # Scale production to match roughly or just dual axis
        sns.lineplot(
            data=df_macro,
            x="tick",
            y=metric_col,
            ax=ax2,
            color="orange",
            label="Total Production (GDP)",
            linestyle="--",
        )
        ax2.set_ylabel("Production Volume", color="orange")

    plt.title("Economic Health: Assets vs Production")
    output_path_2 = os.path.join(OUTPUT_DIR, "02_economic_health.png")
    plt.savefig(output_path_2)
    plt.close()
    print(f"[Saved] {output_path_2}")

    # --- Chart 3: Market Price Trends (주식 vs 식량) ---
    print("Generating Chart 3: Market Prices...")
    if not df_market.empty:
        plt.figure(figsize=(12, 6))
        # [Patch] Stock Visualization
        stock_items = [i for i in df_market["item_id"].unique() if "stock" in i]
        food_items = ["basic_food"]

        # Only plot these if they exist in data
        target_items = [
            i for i in food_items + stock_items if i in df_market["item_id"].unique()
        ]

        for item in target_items:
            subset = df_market[df_market["item_id"] == item]
            if not subset.empty:
                plt.plot(subset["tick"], subset["avg_price"], label=item)

        plt.title("Market Price Trends")
        plt.xlabel("Tick")
        plt.ylabel("Average Price")
        plt.legend()
        output_path_3 = os.path.join(OUTPUT_DIR, "03_market_prices.png")
        plt.savefig(output_path_3)
        plt.close()
        print(f"[Saved] {output_path_3}")

    # --- Chart 4: Trade Volume (거래량 - 유동성 함정 확인) ---
    print("Generating Chart 4: Trade Volume...")
    if not df_market.empty:
        plt.figure(figsize=(12, 6))

        # Filter for key items to avoid clutter if many items exist
        key_items = ["basic_food", "labor", "stock", "clothing"]
        available_items = df_market["item_id"].unique()

        for item in available_items:
            # Visualize all or just key items? All is safer for diagnosis.
            subset = df_market[df_market["item_id"] == item]
            if len(subset) > 0:
                plt.plot(
                    subset["tick"],
                    subset["trade_volume"],
                    label=f"{item} Vol",
                    linestyle=":",
                )

        plt.title("Liquidity Trap Check: Trade Volume")
        plt.xlabel("Tick")
        plt.ylabel("Volume")
        plt.legend()
        output_path_4 = os.path.join(OUTPUT_DIR, "04_trade_volume.png")
        plt.savefig(output_path_4)
        plt.close()
        print(f"[Saved] {output_path_4}")

    print("\nAnalysis Complete! 🚀")
    print(f"Check the report images in: {os.path.abspath(OUTPUT_DIR)}")


if __name__ == "__main__":
    analyze_simulation()
