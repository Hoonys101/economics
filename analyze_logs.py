import csv

def analyze_aid_log(filepath):
    is_trained_counts = {'True': 0, 'False': 0}
    predicted_rewards = []

    with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader) # Skip header row

        # Find column indices
        try:
            is_trained_idx = header.index('is_trained')
            predicted_reward_idx = header.index('predicted_reward')
            method_name_idx = header.index('method_name')
            message_idx = header.index('message')
        except ValueError as e:
            print(f"Error: Missing expected column in CSV header: {e}")
            return

        for i, row in enumerate(reader):
            try:
                if row[method_name_idx] == 'AIDecision':
                    # Process is_trained for all AIDecision logs
                    is_trained_val = row[is_trained_idx]
                    if is_trained_val in is_trained_counts:
                        is_trained_counts[is_trained_val] += 1

                    # Process predicted_reward only for specific messages
                    message_content = row[message_idx]
                    if "Predicted reward for candidate orders:" in message_content or \
                       "Best orders found with predicted reward:" in message_content:
                        predicted_reward_val_str = row[predicted_reward_idx]
                        if predicted_reward_val_str:
                            predicted_rewards.append(float(predicted_reward_val_str))

            except (IndexError, ValueError):
                # Handle rows that might not have all columns or have malformed data
                # print(f"Skipping malformed row {i+2}: {e}")
                pass
                # print(f"Skipping malformed row {i+2}: {e}")
                continue

    print("--- AI Decision Log Analysis ---")
    print("Is Trained Status:")
    for status, count in is_trained_counts.items():
        print(f"  {status}: {count}")

    if predicted_rewards:
        print("Predicted Rewards:")
        print(f"  Total entries: {len(predicted_rewards)}")
        print(f"  Min: {min(predicted_rewards):.2f}")
        print(f"  Max: {max(predicted_rewards):.2f}")
        print(f"  Average: {sum(predicted_rewards) / len(predicted_rewards):.2f}")
    else:
        print("No predicted reward data found.")

if __name__ == "__main__":
    log_filepath = "C:\\coding\\economics\\logs\\simulation_log_AIDecision.csv"
    analyze_aid_log(log_filepath)
