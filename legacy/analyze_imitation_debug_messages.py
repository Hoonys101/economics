import pandas as pd
import os

TEMP_DIR = "utils/temp"

def analyze_imitation_debug_messages():
    message_counts = {
        "Current Imitation Need": 0,
        "Social Status": 0,
        "Active households count": 0,
        "Top households count": 0,
        "Luxury goods in target": 0,
        "Attempting to buy": 0, # This is the key one we're looking for
        "Other": 0
    }

    print(f"Analyzing logs in: {os.getcwd()}")
    print(f"Looking for files in: {TEMP_DIR}")
    
    if not os.path.exists(TEMP_DIR):
        print(f"Error: Directory {TEMP_DIR} does not exist.")
        return

    files_found = 0
    for filename in os.listdir(TEMP_DIR):
        if filename.startswith("imitation_debug_tick_") and filename.endswith(".csv"):
            files_found += 1
            filepath = os.path.join(TEMP_DIR, filename)
            print(f"Processing file: {filepath}")
            try:
                df = pd.read_csv(filepath)
                if df.empty:
                    print(f"  File {filename} is empty.")
                    continue
                print(f"  Read {len(df)} rows from {filename}.")
                for message in df['message']:
                    if "Current Imitation Need" in message:
                        message_counts["Current Imitation Need"] += 1
                    elif "Social Status" in message:
                        message_counts["Social Status"] += 1
                    elif "Active households count" in message:
                        message_counts["Active households count"] += 1
                    elif "Top households count" in message:
                        message_counts["Top households count"] += 1
                    elif "Luxury goods in target" in message:
                        message_counts["Luxury goods in target"] += 1
                    elif "Attempting to buy" in message:
                        message_counts["Attempting to buy"] += 1
                    else:
                        message_counts["Other"] += 1
            except Exception as e:
                print(f"Error reading {filepath}: {e}")

    if files_found == 0:
        print(f"No CSV files found in {TEMP_DIR} matching the pattern.")

    print("\n--- Imitation Debug Message Summary ---")
    for msg_type, count in message_counts.items():
        print(f"{msg_type}: {count}")

if __name__ == "__main__":
    analyze_imitation_debug_messages()
