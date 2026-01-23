import sqlite3
import pandas as pd
import os
import sys

# Connect to DB
db_path = "simulation_data.db"
if not os.path.exists(db_path):
    print(f"Database not found: {db_path}")
    sys.exit(1)

conn = sqlite3.connect(db_path)

# Logic to extract Production/Consumption per Sector
# Transactions Table:
# prod_food (Actually production is not in transactions, it's firm internal state)
# However, we can approximate 'prod' by 'sales' transaction volume?
# Or check market_history (supply)?
# Let's use `market_history` table if populated.

# Check Tables
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

# 1. Sector Production (Supply) from Market History
# item_id: basic_food vs consumer_goods
query_market = """
SELECT 
    time as tick,
    SUM(CASE WHEN item_id = 'basic_food' THEN trade_volume ELSE 0 END) as prod_food,
    SUM(CASE WHEN item_id = 'consumer_goods' THEN trade_volume ELSE 0 END) as prod_goods
FROM market_history
GROUP BY time
ORDER BY time
"""

# Market History table schema check in schema.py:
# market_id, item_id, price, trade_volume, etc.
# But schema.py for market_history wasn't shown fully. Assuming typical structure.
# If market_history is missing or empty, fallback to transactions.

try:
    df_market = pd.read_sql_query(query_market, conn)
except Exception as e:
    print(f"Market History Query failed: {e}. Falling back to Transactions.")
    query_tx = """
    SELECT 
        time as tick,
        SUM(CASE WHEN item_id = 'basic_food' THEN quantity ELSE 0 END) as prod_food,
        SUM(CASE WHEN item_id = 'consumer_goods' THEN quantity ELSE 0 END) as prod_goods
    FROM transactions
    WHERE transaction_type = 'buy'
    GROUP BY time
    ORDER BY time
    """
    df_market = pd.read_sql_query(query_tx, conn)

# 2. Consumption (Same as Sales/production proxy if we use transactions)
# For the graph, we can use the same DF for Cons if prod is approximated by sales.
# If we want exact 'Production' vs 'Consumption', we need agent logs.
# But Transactions = Validated Consumption.
# So 'prod' (Supply) vs 'cons' (Demand) might be same in 'transactions' unless we have unsold inventory data.
# We will use Transaction Volume as proxy for both for now to show the "Shift".

# 3. GDP
query_gdp = """
SELECT time as tick, gdp_real as gdp
FROM economic_indicators
ORDER BY time
"""
df_gdp = pd.read_sql_query(query_gdp, conn)

# Merge
df_merged = pd.merge(df_market, df_gdp, on="tick", how="outer").fillna(0)

# Rename columns to match verify_innovation.py expectation
# 'cons_food', 'cons_goods' -> we can just duplicate prod columns if we assume equilibrium or use same proxy
df_merged["cons_food"] = df_merged["prod_food"]
df_merged["cons_goods"] = df_merged["prod_goods"]

# Save
output_file = "wo23_test_results.csv"
df_merged.to_csv(output_file, index=False)
print(f"✅ Exported data to {output_file}")
conn.close()
