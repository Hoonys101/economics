import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# 파일 경로를 실제 환경에 맞게 수정하세요.
log_filepath = 'C:\\coding\\economics\\logs\\simulation_log_StandardLog.csv'

try:
    df = pd.read_csv(log_filepath)

    logging.info("--- AI Decision Log Analysis ---")

    # is_trained 상태 확인
    if 'is_trained' in df.columns:
        logging.info("\nIs Trained Status:")
        logging.info(df['is_trained'].value_counts())
    else:
        logging.info("\n'is_trained' column not found.")

    # predicted_reward 값 분석
    if 'predicted_reward' in df.columns:
        # 숫자 변환 시도, 변환 불가 값은 NaT(Not a Time)이 아닌 NaN(Not a Number)으로 처리
        rewards = pd.to_numeric(df['predicted_reward'], errors='coerce').dropna()
        if not rewards.empty:
            logging.info("\nPredicted Rewards Statistics:")
            logging.info(f"  Total entries: {len(rewards)}")
            logging.info(f"  Min: {rewards.min():.2f}")
            logging.info(f"  Max: {rewards.max():.2f}")
            logging.info(f"  Average: {rewards.mean():.2f}")
        else:
            logging.info("\nNo valid predicted reward data found.")
    else:
        logging.info("\n'predicted_reward' column not found.")

    # 'food' 관련 의사결정 분석
    if 'item' in df.columns and 'predicted_reward' in df.columns:
        food_decisions = df[df['item'] == 'food'].copy()
        if not food_decisions.empty:
            logging.info("\nFood-related Decisions:")
            food_rewards = pd.to_numeric(food_decisions['predicted_reward'], errors='coerce').dropna()
            if not food_rewards.empty:
                logging.info(f"  Total food decisions with reward: {len(food_rewards)}")
                logging.info(f"  Average predicted reward for food: {food_rewards.mean():.2f}")
            else:
                logging.info("  No valid predicted reward data for food-related decisions.")
        else:
            logging.info("\nNo food-related decisions found.")

except FileNotFoundError:
    logging.error(f"Error: Log file not found at {log_filepath}")
except Exception as e:
    logging.error(f"An error occurred: {e}")
