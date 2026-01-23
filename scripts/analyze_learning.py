import pandas as pd
import matplotlib.pyplot as plt
import re
import os


def parse_logs(log_file):
    rewards = []
    ticks = []

    pattern = re.compile(r"GOV_AI_LEARN \| Tick: (\d+) \| Reward: ([-.\d]+)")

    if not os.path.exists(log_file):
        print(f"Log file {log_file} not found.")
        return None, None

    with open(log_file, "r") as f:
        for line in f:
            match = pattern.search(line)
            if match:
                ticks.append(int(match.group(1)))
                rewards.append(float(match.group(2)))

    return ticks, rewards


def plot_learning_curve(ticks, rewards, output_file="reports/learning_curve.png"):
    if not ticks:
        print("No learning data found in logs.")
        return

    df = pd.DataFrame({"tick": ticks, "reward": rewards})
    df = df.sort_values("tick")

    # Rolling Average (Window 50)
    df["rolling_reward"] = df["reward"].rolling(window=50, min_periods=1).mean()

    plt.figure(figsize=(12, 6))
    plt.plot(df["tick"], df["reward"], alpha=0.3, label="Raw Reward", color="gray")
    plt.plot(
        df["tick"],
        df["rolling_reward"],
        label="Rolling Average (50)",
        color="blue",
        linewidth=2,
    )

    # Phase Markers
    plt.axvline(x=300, color="red", linestyle="--", alpha=0.5)
    plt.text(
        150,
        plt.ylim()[1] * 0.9,
        "Phase 1: Chaos",
        color="red",
        horizontalalignment="center",
    )
    plt.axvline(x=700, color="green", linestyle="--", alpha=0.5)
    plt.text(
        500,
        plt.ylim()[1] * 0.9,
        "Phase 2: Convergence",
        color="green",
        horizontalalignment="center",
    )
    plt.text(
        850,
        plt.ylim()[1] * 0.9,
        "Phase 3: Stability",
        color="blue",
        horizontalalignment="center",
    )

    plt.title("Smart Leviathan: Operation Awakening Learning Curve")
    plt.xlabel("Ticks")
    plt.ylabel("Reward (Macro Stability Score)")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend()

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file)
    print(f"Learning curve saved to {output_file}")


if __name__ == "__main__":
    log_path = "logs/simulation.log"
    ticks, rewards = parse_logs(log_path)
    plot_learning_curve(ticks, rewards)
