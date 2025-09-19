import pandas as pd

def analyze_aid_log_pandas(filepath):
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"Error reading CSV with pandas: {e}")
        return

    print("---\n--- AI Decision Log Analysis (Pandas) ---")
    print("DataFrame Head:")
    print(df.head())
    print("\nDataFrame Info:")
    df.info()
    print("\nDataFrame Columns:")
    print(df.columns)

    # 1. Check is_trained status
    if 'is_trained' in df.columns:
        is_trained_counts = df['is_trained'].value_counts()
        print("\nIs Trained Status:")
        for status, count in is_trained_counts.items():
            print(f"  {status}: {count}")
    else:
        print("'is_trained' column not found.")

    # 2. Analyze predicted_reward values
    if 'predicted_reward' in df.columns:
        predicted_rewards_series = df['predicted_reward'].dropna() # Drop NaN values
        if not predicted_rewards_series.empty:
            print("Predicted Rewards:")
            print(f"  Total entries: {len(predicted_rewards_series)}")
            print(f"  Min: {predicted_rewards_series.min():.2f}")
            print(f"  Max: {predicted_rewards_series.max():.2f}")
            print(f"  Average: {predicted_rewards_series.mean():.2f}")
        else:
            print("No predicted reward data found (after dropping NaN).")
    else:
        print("'predicted_reward' column not found.")

    # 3. Relate to food market
    if 'item' in df.columns and 'predicted_reward' in df.columns:
        food_decisions = df[df['item'] == 'food']
        if not food_decisions.empty:
            print("\nFood-related Decisions:")
            food_rewards = food_decisions['predicted_reward'].dropna()
            if not food_rewards.empty:
                print(f"  Total food-related decisions with predicted reward: {len(food_rewards)}")
                print(f"  Min predicted reward for food: {food_rewards.min():.2f}")
                print(f"  Max predicted reward for food: {food_rewards.max():.2f}")
                print(f"  Average predicted reward for food: {food_rewards.mean():.2f}")
            else:
                print("No predicted reward data for food-related decisions.")
        else:
            print("No food-related decisions found.")
    else:
        print("'item' or 'predicted_reward' column not found for food analysis.")

if __name__ == "__main__":
    log_filepath = "C:\\coding\\economics\\logs\\simulation_log_AIDecision.csv"
    analyze_aid_log_pandas(log_filepath)
