
import re
import os
import statistics

LOG_FILE = "simulation.log"
OUTPUT_FILE = "reports/learning_report.txt"

def generate_learning_report():
    """
    Parses the simulation log to extract AI rewards and generates a statistical text report.
    Replaces image generation to avoid binary conflicts.
    """
    rewards = {}
    
    print(f"Parsing log file: {LOG_FILE}")
    if not os.path.exists(LOG_FILE):
        print(f"Error: Log file not found at {LOG_FILE}")
        return

    # Regex to capture Reward and Tick
    log_pattern = re.compile(r"GOV_AI_LEARN \| Reward: ([\-0-9\.]+) \| Tick: (\d+)")

    with open(LOG_FILE, "r") as f:
        for line in f:
            match = log_pattern.search(line)
            if match:
                try:
                    r_val = float(match.group(1))
                    tick = int(match.group(2))
                    rewards[tick] = r_val
                except (ValueError, IndexError):
                    continue

    if not rewards:
        print("No 'GOV_AI_LEARN' records found.")
        return

    # Analyze Shocks
    # Shock 1: Inflation (Tick 200) -> Analyze 150-199 vs 200-249
    # Shock 2: Recession (Tick 600) -> Analyze 550-599 vs 600-649
    
    def get_avg(start, end):
        vals = [rewards[t] for t in range(start, end) if t in rewards]
        return statistics.mean(vals) if vals else None

    s1_pre = get_avg(150, 200)
    s1_post = get_avg(200, 250)
    
    s2_pre = get_avg(550, 600)
    s2_post = get_avg(600, 650)
    
    report_lines = []
    report_lines.append("=== AI Learning Analysis Report (Operation Show Therapy) ===")
    
    if s1_pre is not None and s1_post is not None:
        delta1 = s1_post - s1_pre
        report_lines.append(f"Shock 1 (Inflation @ 200): Pre={s1_pre:.2f}, Post={s1_post:.2f}, Delta={delta1:.2f}")
    else:
        report_lines.append("Shock 1: Insufficient data.")

    if s2_pre is not None and s2_post is not None:
        delta2 = s2_post - s2_pre
        report_lines.append(f"Shock 2 (Recession @ 600): Pre={s2_pre:.2f}, Post={s2_post:.2f}, Delta={delta2:.2f}")
    else:
        report_lines.append("Shock 2: Insufficient data.")
        
    full_report = "\n".join(report_lines)
    print(full_report)
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write(full_report)
    print(f"\nReport saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_learning_report()
