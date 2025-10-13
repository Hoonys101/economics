import sqlite3
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def analyze_food_market_data(db_path="simulation_data.db"):
    conn = sqlite3.connect(db_path)
    
    # Fetch economic indicators
    economic_indicators_df = pd.read_sql_query("SELECT time, food_avg_price, food_trade_volume FROM economic_indicators", conn)
    
    conn.close()
    
    if economic_indicators_df.empty:
        logging.info("No economic indicator data found.")
        return None

    # Calculate average food price and trade volume
    avg_food_price = economic_indicators_df['food_avg_price'].mean()
    avg_food_trade_volume = economic_indicators_df['food_trade_volume'].mean()
    
    logging.info(f"Average Food Price: {avg_food_price:.2f}")
    logging.info(f"Average Food Trade Volume: {avg_food_trade_volume:.2f}")
    
    return {
        "avg_food_price": avg_food_price,
        "avg_food_trade_volume": avg_food_trade_volume
    }

if __name__ == "__main__":
    results = analyze_food_market_data()
    if results:
        with open("food_market_analysis_baseline.txt", "w") as f:
            f.write(f"Average Food Price: {results['avg_food_price']:.2f}\n")
            f.write(f"Average Food Trade Volume: {results['avg_food_trade_volume']:.2f}\n")
        logging.info("Analysis saved to food_market_analysis_baseline.txt")
