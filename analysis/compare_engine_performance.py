import sqlite3
import os
import argparse
import statistics
from typing import List, Dict, Any, Optional

DB_PATH = "simulation_data.db"


def get_connection(db_path: str = DB_PATH):
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found.")
        return None
    return sqlite3.connect(db_path)


def list_runs(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT run_id, start_time, description FROM simulation_runs ORDER BY run_id DESC LIMIT 10"
    )
    runs = cursor.fetchall()
    print("\n--- Recent Simulation Runs ---")
    print(f"{'Run ID':<10} {'Start Time':<25} {'Description'}")
    print("-" * 50)
    for run in runs:
        description = run[2] if run[2] else "N/A"
        print(f"{run[0]:<10} {run[1]:<25} {description}")
    print("-" * 50)
    return runs


def get_run_metrics(conn: sqlite3.Connection, run_id: int) -> Dict[str, Any]:
    metrics = {}
    cursor = conn.cursor()

    # 1. Economic Indicators
    cursor.execute(
        """
        SELECT 
            AVG(total_consumption), 
            AVG(total_household_assets), 
            AVG(total_firm_assets),
            AVG(unemployment_rate),
            AVG(food_avg_price)
        FROM economic_indicators 
        WHERE run_id = ?
    """,
        (run_id,),
    )
    row = cursor.fetchone()
    if row:
        metrics["avg_gdp"] = row[0]
        metrics["avg_household_assets"] = row[1]
        metrics["avg_firm_assets"] = row[2]
        metrics["avg_unemployment"] = row[3]
        metrics["avg_food_price"] = row[4]

    # 2. Agent Needs (from AgentState) - Optional, takes longer
    # Assuming we want average survival need for households
    cursor.execute(
        """
        SELECT AVG(needs_survival)
        FROM agent_states
        WHERE run_id = ? AND agent_type = 'Household'
    """,
        (run_id,),
    )
    row = cursor.fetchone()
    if row and row[0] is not None:
        metrics["avg_household_survival_need"] = row[0]
    else:
        metrics["avg_household_survival_need"] = 0.0

    return metrics


def compare_runs(conn: sqlite3.Connection, run_id_1: int, run_id_2: int):
    print(f"\n--- Comparing Run {run_id_1} vs Run {run_id_2} ---")

    metrics1 = get_run_metrics(conn, run_id_1)
    metrics2 = get_run_metrics(conn, run_id_2)

    if not metrics1 or not metrics2:
        print("Error: Could not retrieve metrics for one or both runs.")
        return

    print(
        f"{'Metric':<30} | {'Run ' + str(run_id_1):<15} | {'Run ' + str(run_id_2):<15} | {'Diff (%)':<10}"
    )
    print("-" * 80)

    compare_keys = [
        ("Avg GDP", "avg_gdp"),
        ("Avg Household Assets", "avg_household_assets"),
        ("Avg Firm Assets", "avg_firm_assets"),
        ("Avg Unemployment Rate", "avg_unemployment"),
        ("Avg Food Price", "avg_food_price"),
        ("Avg Survival Need", "avg_household_survival_need"),
    ]

    for label, key in compare_keys:
        val1 = metrics1.get(key, 0) or 0
        val2 = metrics2.get(key, 0) or 0

        diff_pct = 0.0
        if val1 != 0:
            diff_pct = ((val2 - val1) / val1) * 100
        elif val2 != 0:
            diff_pct = 100.0 if val2 > 0 else -100.0

        print(f"{label:<30} | {val1:<15.2f} | {val2:<15.2f} | {diff_pct:+.2f}%")

    print("-" * 80)


def main():
    parser = argparse.ArgumentParser(description="Compare simulation run performance.")
    parser.add_argument("run1", type=int, nargs="?", help="Run ID 1")
    parser.add_argument("run2", type=int, nargs="?", help="Run ID 2")

    args = parser.parse_args()

    conn = get_connection()
    if not conn:
        return

    try:
        if args.run1 is None or args.run2 is None:
            runs = list_runs(conn)
            if len(runs) >= 2:
                print("Tip: Provide two Run IDs as arguments to compare specific runs.")
                # Auto-select last two if available
                r1 = runs[0][0]
                r2 = runs[1][0]
                compare_runs(conn, r2, r1)  # Compare older (r2) vs newer (r1)
            else:
                print("Not enough runs to compare.")
        else:
            compare_runs(conn, args.run1, args.run2)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
