import sqlite3
import pandas as pd

def extract_meta():
    conn = sqlite3.connect('simulation_data.db')
    df = pd.read_sql_query('SELECT time, total_inventory, total_production, total_consumption, total_household_assets, total_firm_assets FROM economic_indicators WHERE run_id = (SELECT MAX(run_id) FROM simulation_runs)', conn)
    
    peak_inv = df["total_inventory"].max()
    peak_tick = df.loc[df["total_inventory"].idxmax(), "time"]
    zero_inv_tick = df[df["total_inventory"] <= 0.1]["time"].min() if not df[df["total_inventory"] <= 0.1].empty else "Never"
    
    total_prod = df["total_production"].sum()
    total_cons = df["total_consumption"].sum()
    
    print(f"Inventory Analysis:")
    print(f"- Peak Inventory: {peak_inv:.2f} units at Tick {peak_tick}")
    print(f"- Inventory Exhaustion: Tick {zero_inv_tick}")
    print(f"- Total Production: {total_prod:.2f} units")
    print(f"- Total Consumption: {total_cons:.2f} units")
    print(f"- Gap: {total_prod - total_cons:.2f} units")
    
    final_hh = df.iloc[-1]["total_household_assets"]
    final_firm = df.iloc[-1]["total_firm_assets"]
    print(f"\nLiquidity Analysis (Tick 1000):")
    print(f"- Household Cash: {final_hh:.2f}")
    print(f"- Firm Cash: {final_firm:.2f}")
    
    conn.close()

if __name__ == "__main__":
    extract_meta()
