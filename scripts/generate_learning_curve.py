
import re
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os

LOG_FILE = "simulation.log"
OUTPUT_FILE = "reports/learning_curve.png"

def generate_learning_curve():
    """
    Parses the simulation log to extract AI rewards and generate a learning curve plot.
    """
    rewards = []
    ticks = []

    # Regex to capture tick and reward from the log line
    # Example Line: 2026-01-13 04:32:44,870 - simulation.agents.government - DEBUG - GOV_AI_LEARN | Reward: -0.00123 ...
    # We need to get the reward value after "Reward: "
    reward_pattern = re.compile(r"GOV_AI_LEARN \| Reward: ([\-0-9\.]+)")
    tick_pattern = re.compile(r"tick=(\d+)")

    print(f"Parsing log file: {LOG_FILE}")
    if not os.path.exists(LOG_FILE):
        print(f"Error: Log file not found at {LOG_FILE}")
        return

    with open(LOG_FILE, "r") as f:
        for line in f:
            reward_match = reward_pattern.search(line)

            if reward_match:
                try:
                    # The tick is not in the GOV_AI_LEARN log message itself.
                    # It's in the log record's metadata if configured.
                    # A simpler approach is to find a preceding log from the same tick that has it.
                    # Or, since decisions happen every 30 ticks, we can approximate it.
                    # Let's assume the order is preserved and just count the occurrences.
                    reward = float(reward_match.group(1))
                    rewards.append(reward)
                except (ValueError, IndexError):
                    continue

    if not rewards:
        print("No 'GOV_AI_LEARN' records found in the log. Cannot generate learning curve.")
        return

    # Decisions are made every 30 ticks, starting from tick 0 or 30.
    # Let's assume the first one is at tick 30.
    ticks = [i * 30 for i in range(1, len(rewards) + 1)]

    df = pd.DataFrame({'tick': ticks, 'reward': rewards})

    # Calculate a rolling average to smooth the curve
    df['reward_smoothed'] = df['reward'].rolling(window=5, min_periods=1).mean()

    print(f"Found {len(df)} learning data points.")

    # Generate Plot
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(12, 7))

    # Raw reward scatter plot
    plt.scatter(df['tick'], df['reward'], alpha=0.3, label='Raw Reward per Decision', color='lightblue')

    # Smoothed learning curve
    plt.plot(df['tick'], df['reward_smoothed'], label='Learning Curve (5-period SMA)', color='blue', linewidth=2)

    plt.title('Government AI Learning Curve')
    plt.xlabel('Simulation Tick')
    plt.ylabel('Macro Stability Reward')
    plt.legend()
    plt.grid(True)

    # Ensure reports directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    plt.savefig(OUTPUT_FILE)
    print(f"Learning curve saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_learning_curve()
