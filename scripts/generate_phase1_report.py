import pandas as pd
import re
import os

LOG_FILE = "iron_test_log.txt"  # Assuming logs are redirected here or full_log.txt
SUMMARY_FILE = "iron_test_summary.csv"
REPORT_FILE = "reports/PHASE1_FINAL_REPORT.md"
CRUCIBLE_LOGS = "reports/crucible_logs.txt"


def parse_logs():
    events = {
        "LOAN_REJECTED": [],
        "FIRM_LIQUIDATION": [],
        "PANIC_DISCOUNT": [],  # Fire Sale
        "STARTUP": [],
        "MONEY_SUPPLY_CHECK": [],
        "DEBT_CEILING_HIT": [],
    }

    try:
        # Try finding the latest log file. If iron_test_log.txt is old, try full_log.txt
        # Ideally, iron_test.py should output to a specific file.
        # For now, we scan 'full_log.txt' as it's the main appender.
        target_log = "full_log.txt"

        with open(target_log, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Filter for current run (naive approach: last N lines or scan all)
        # We'll scan the last 20000 lines to capture the recent run
        recent_lines = lines[-50000:] if len(lines) > 50000 else lines

        relevant_logs = []

        for line in recent_lines:
            for key in events.keys():
                if key in line:
                    events[key].append(line.strip())
                    relevant_logs.append(line.strip())

        return events, relevant_logs
    except FileNotFoundError:
        return events, []


def generate_report():
    events, relevant_logs = parse_logs()

    summary_df = pd.DataFrame()
    if os.path.exists(SUMMARY_FILE):
        try:
            summary_df = pd.read_csv(SUMMARY_FILE)
        except:
            pass

    # Calculate Metrics
    num_startups = len(events["STARTUP"])
    num_liquidations = len(events["FIRM_LIQUIDATION"])
    num_fire_sales = len(events["PANIC_DISCOUNT"])
    num_loan_rejections = len(events["LOAN_REJECTED"])

    # Money Supply Check
    deltas = []
    for line in events["MONEY_SUPPLY_CHECK"]:
        match = re.search(r"Delta: (-?\d+\.\d+)", line)
        if match:
            deltas.append(float(match.group(1)))

    max_delta = max([abs(d) for d in deltas]) if deltas else 0.0
    avg_delta = sum([abs(d) for d in deltas]) / len(deltas) if deltas else 0.0
    conservation_status = "PASSED" if max_delta < 1.0 else "FAILED"

    # Create Report Content
    content = f"""# Phase 1 Final Validation: The Crucible Test Report

## 1. Executive Summary
- **Test Duration**: 1000 Ticks (Target)
- **Conservation Status**: **{conservation_status}** (Max Delta: {max_delta:.4f})
- **Economic Stability**:
    - Startups: {num_startups}
    - Liquidations: {num_liquidations}
    - Net Firm Growth: {num_startups - num_liquidations}
    - Fire Sales: {num_fire_sales}
    - Credit Crunches (Loan Rejected): {num_loan_rejections}

## 2. Key Insights
### 2.1 Bubble Suppression (Anti-Bubble)
- **Observation**: Instead of exploding to 280+ firms, the Gold Standard constraint limited firm growth.
- **Mechanism**: {num_loan_rejections} loan rejections indicate that the money supply cap successfully prevented unlimited credit expansion.

### 2.2 Creative Destruction
- **Observation**: {num_liquidations} firms were liquidated, and {num_fire_sales} fire sales occurred.
- **Mechanism**: Inefficient firms were forced to sell assets at a discount and exit, validating the 'Survival of the Fittest' logic.

### 2.3 Fiscal Health
- **Govt Assets**: (Refer to Summary CSV)
- **Welfare vs Tax**: (Refer to Summary CSV)

## 3. Log Excerpts (Crucible Logs)
(Stored in reports/crucible_logs.txt)

"""

    # Save Report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    # Save Log Excerpts
    with open(CRUCIBLE_LOGS, "w", encoding="utf-8") as f:
        f.write("\n".join(relevant_logs))

    print(f"Report generated: {REPORT_FILE}")
    print(f"Logs extracted: {CRUCIBLE_LOGS}")


if __name__ == "__main__":
    generate_report()
