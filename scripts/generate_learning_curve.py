
import re
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os

LOG_FILE = "simulation.log"
OUTPUT_FILE = "reports/learning_curve_v2.png"

def generate_learning_curve():
    """
    Parses the simulation log to extract AI rewards and generate a learning curve plot.
    """
    rewards = []
    ticks = []

    # Corrected Regex to capture Reward and Tick
    log_pattern = re.compile(r"GOV_AI_LEARN \| Reward: (-?[\d\.]+) \| Tick: (\d+)")
    
    print(f"Parsing log file: {LOG_FILE}")
    if not os.path.exists(LOG_FILE):
        print(f"Error: Log file not found at {LOG_FILE}")
        return

    with open(LOG_FILE, "r") as f:
        for line in f:
            match = log_pattern.search(line)
            if match:
                try:
                    rewards.append(float(match.group(1)))
                    ticks.append(int(match.group(2)))
                except (ValueError, IndexError):
                    continue

    if not rewards:
        print("No 'GOV_AI_LEARN' records found.")
        return

    df = pd.DataFrame({'tick': ticks, 'reward': rewards})
    
    df['reward_smoothed'] = df['reward'].rolling(window=5, min_periods=1).mean()

    # Plot
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax1 = plt.subplots(figsize=(12, 7))

    ax1.scatter(df['tick'], df['reward'], alpha=0.3, color='lightblue', label='Raw Reward')
    ax1.plot(df['tick'], df['reward_smoothed'], color='blue', linewidth=2, label='Smoothed Reward (SMA)')

    # Add vertical lines for chaos events
    ax1.axvline(x=200, color='r', linestyle='--', label='Inflation Shock (Tick 200)')
    ax1.axvline(x=600, color='r', linestyle='--', label='Recession Shock (Tick 600)')

    ax1.set_xlabel('Tick')
    ax1.set_ylabel('Reward')
    ax1.tick_params(axis='y')

    plt.title('Government AI Learning Curve (Operation Shock Therapy)')
    ax1.legend()
    ax1.grid(True)

    # Ensure reports directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    plt.savefig(OUTPUT_FILE)
    print(f"Learning curve saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_learning_curve()
