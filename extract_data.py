import csv
import io
from utils.logger import Logger
logger = Logger()

def extract_data(filepath):
    with open(filepath, 'rb') as binary_file:
        # Wrap the binary file in a TextIOWrapper to specify encoding
        text_file = io.TextIOWrapper(binary_file, encoding='utf-8')
        reader = csv.reader(text_file)
        header = next(reader) # Skip header row
        logger.debug(log_type="DataExtraction", tick=None, agent_type="Utility", agent_id=None, method_name="extract_data", message=f"Header: {header}", header=header)

        try:
            is_trained_idx = header.index('is_trained')
            predicted_reward_idx = header.index('predicted_reward')
            method_name_idx = header.index('method_name')
            message_idx = header.index('message')
        except ValueError as e:
            logger.error(log_type="DataExtraction", tick=None, agent_type="Utility", agent_id=None, method_name="extract_data", message=f"Missing expected column in CSV header: {e}", error_message=str(e))
            return

        for row in reader:
            logger.debug(log_type="DataExtraction", tick=None, agent_type="Utility", agent_id=None, method_name="extract_data", message="Reader is ready. Starting row processing.")
            logger.debug(log_type="DataExtraction", tick=None, agent_type="Utility", agent_id=None, method_name="extract_data", message=f"Processing row. Method Name: {row[method_name_idx] if len(row) > method_name_idx else 'N/A'}", row_data=row)
            try:
                if row[method_name_idx] == 'AIDecision':
                    # Extract is_trained
                    is_trained_val = row[is_trained_idx]
                    logger.debug(log_type="DataExtraction", tick=None, agent_type="Utility", agent_id=None, method_name="extract_data", message=f"is_trained:{is_trained_val}", is_trained=is_trained_val)

                    # Extract predicted_reward for specific messages
                    message_content = row[message_idx]
                    if "Predicted reward for candidate orders:" in message_content or \
                       "Best orders found with predicted reward:" in message_content:
                        predicted_reward_val_str = row[predicted_reward_idx]
                        if predicted_reward_val_str:
                            logger.debug(log_type="DataExtraction", tick=None, agent_type="Utility", agent_id=None, method_name="extract_data", message=f"predicted_reward:{predicted_reward_val_str}", predicted_reward=predicted_reward_val_str)

            except IndexError:
                logger.error(log_type="DataExtraction", tick=None, agent_type="Utility", agent_id=None, method_name="extract_data", message=f"IndexError caught for row: {row}", row_data=row)
                # Skip malformed rows that don't have enough columns
                continue

if __name__ == "__main__":
    log_filepath = "C:\\coding\\economics\\logs\\simulation_log_AIDecision.csv"
    extract_data(log_filepath)
