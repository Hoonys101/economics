import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def analyze_aid_log_pandas(filepath):
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        logging.error(f"Error reading CSV with pandas: {e}")
        return

    logging.info("---\n--- AI Decision Log Analysis (Pandas) ---")
    logging.info("DataFrame Head:")
    logging.info(df.head())
    logging.info("\nDataFrame Info:")
    df.info()
    logging.info("\nDataFrame Columns:")
    logging.info(df.columns)

    # 1. Check is_trained status
    if 'is_trained' in df.columns:
        is_trained_counts = df['is_trained'].value_counts()
        logging.info("\nIs Trained Status:")
        for status, count in is_trained_counts.items():
            logging.info(f"  {status}: {count}")
    else:
        logging.info("'is_trained' column not found.")

    # 2. Analyze predicted_reward values
    if 'predicted_reward' in df.columns:
        predicted_rewards_series = df['predicted_reward'].dropna() # Drop NaN values
        if not predicted_rewards_series.empty:
            logging.info("Predicted Rewards:")
            logging.info(f"  Total entries: {len(predicted_rewards_series)}")
            logging.info(f"  Min: {predicted_rewards_series.min():.2f}")
            logging.info(f"  Max: {predicted_rewards_series.max():.2f}")
            logging.info(f"  Average: {predicted_rewards_series.mean():.2f}")
        else:
            logging.info("No predicted reward data found (after dropping NaN).")
    else:
        logging.info("'predicted_reward' column not found.")

    # 3. Relate to food market
    if 'item' in df.columns and 'predicted_reward' in df.columns:
        food_decisions = df[df['item'] == 'food']
        if not food_decisions.empty:
            logging.info("\nFood-related Decisions:")
            food_rewards = food_decisions['predicted_reward'].dropna()
            if not food_rewards.empty:
                logging.info(f"  Total food-related decisions with predicted reward: {len(food_rewards)}")
                logging.info(f"  Min predicted reward for food: {food_rewards.min():.2f}")
                logging.info(f"  Max predicted reward for food: {food_rewards.max():.2f}")
                logging.info(f"  Average predicted reward for food: {food_rewards.mean():.2f}")
            else:
                logging.info("No predicted reward data for food-related decisions.")
        else:
            logging.info("No food-related decisions found.")
    else:
        logging.info("'item' or 'predicted_reward' column not found for food analysis.")

if __name__ == "__main__":
    log_filepath = "C:\\coding\\economics\\logs\\simulation_log_AIDecision.csv"
    analyze_aid_log_pandas(log_filepath)
