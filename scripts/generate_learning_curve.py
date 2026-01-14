
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

    # Updated Regex to capture State
    # Example: ... | State: (0, 0, 1, 0) -> ...
    log_pattern = re.compile(r"GOV_AI_LEARN \| Reward: ([\-0-9\.]+) .*\| State: ([\(\)\d, ]+)")
    
    print(f"Parsing log file: {LOG_FILE}")
    if not os.path.exists(LOG_FILE):
        print(f"Error: Log file not found at {LOG_FILE}")
        return

    states = []
    rewards = []

    with open(LOG_FILE, "r") as f:
        for line in f:
            match = log_pattern.search(line)
            if match:
                try:
                    rewards.append(float(match.group(1)))
                    states.append(match.group(2).strip())
                except (ValueError, IndexError):
                    continue

    if not rewards:
        print("No 'GOV_AI_LEARN' records found.")
        return

    # Mock ticks (assuming 30 tick interval)
    ticks = [i * 30 for i in range(1, len(rewards) + 1)]
    df = pd.DataFrame({'tick': ticks, 'reward': rewards, 'state': states})
    
    # Calculate Rolling State Entropy (Variety of states in last 5 steps)
    df['state_diversity'] = df['state'].rolling(window=10).apply(lambda x: len(set(x)), raw=False)

    df['reward_smoothed'] = df['reward'].rolling(window=5, min_periods=1).mean()

    # Plot
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax1 = plt.subplots(figsize=(12, 7))

    ax1.scatter(df['tick'], df['reward'], alpha=0.3, color='lightblue', label='Reward')
    ax1.plot(df['tick'], df['reward_smoothed'], color='blue', linewidth=2, label='Reward (SMA)')
    ax1.set_xlabel('Tick')
    ax1.set_ylabel('Reward', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # Secondary Axis: State Diversity
    ax2 = ax1.twinx()
    ax2.plot(df['tick'], df['state_diversity'], color='orange', linestyle='--', label='State Diversity (10-window)')
    ax2.set_ylabel('Unique States Count', color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')
    ax2.set_ylim(0, 11)  # Max window size + buffer

    plt.title('Government AI: Learning & Sensory Input Check')
    fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9))
    ax1.grid(True)

    # Secondary Axis for State Changes (if any)
    # Since we can't easily parse complex state tuples in this simple script without regex overhaul,
    # let's just note that for now. Future enhancement: Plot unique state count window.

    # Ensure reports directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    plt.savefig(OUTPUT_FILE)
    print(f"Learning curve saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_learning_curve()
