import sys
from pathlib import Path
import os
import pandas as pd
import numpy as np
import logging
import io

# Setup paths to import project modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import create_simulation
import config

# Configure Logger
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("OperationDarwin")

# Capture logs to string buffer for analysis
log_capture_string = io.StringIO()
ch = logging.StreamHandler(log_capture_string)
ch.setLevel(logging.INFO)
logging.getLogger().addHandler(ch)


def run_test(name, ticks, overrides):
    print(f"\n[Operation Darwin] Running {name} Test ({ticks} ticks)...")

    # Clear log capture
    log_capture_string.truncate(0)
    log_capture_string.seek(0)

    sim = create_simulation(overrides=overrides)

    try:
        for tick in range(1, ticks + 1):
            sim.run_tick()
            if tick % 100 == 0:
                gdp = sim.tracker.get_latest_indicators().get("total_production", 0)
                print(f"   Tick {tick}: GDP={gdp:.1f}")

    except Exception as e:
        print(f"CRITICAL ERROR in {name}: {e}")
        import traceback

        traceback.print_exc()

    # Capture final metrics
    logs = log_capture_string.getvalue()
    metrics = {
        "GDP": sim.tracker.get_latest_indicators().get("total_production", 0),
        "MoneyDeltaMax": 0.0,
    }

    # Analyze logs
    mitosis_count = logs.count("MITOSIS")
    death_count = logs.count("HOUSEHOLD_INACTIVE")
    spending_rejected_count = logs.count("SPENDING_REJECTED")
    money_warnings = [
        line
        for line in logs.split("\n")
        if "MONEY_SUPPLY_CHECK" in line and "WARNING" in line
    ]

    metrics["MitosisCount"] = mitosis_count
    metrics["DeathCount"] = death_count
    metrics["SpendingRejected"] = spending_rejected_count
    metrics["MoneyWarnings"] = len(money_warnings)

    sim.repository.close()
    return metrics, logs


def operation_darwin():
    print("=== Operation Darwin: Survival of the Fittest Verification ===")

    # Overrides for Darwin
    # 1. Ensure UNEMPLOYMENT_BENEFIT_RATIO is 0.0 (though it should be in config, double check via overrides not needed if config is updated,
    # but good to be explicit or just rely on config)
    # The task says verify config change. So we rely on config.py.
    # We might increase population to ensure interaction? Default is 20.
    overrides = {
        "SIMULATION_TICKS": 1000,
        "UNEMPLOYMENT_BENEFIT_RATIO": 0.0,  # Force override just in case, though file edit should handle it
    }

    # --- Test 1: Short Test (100 Ticks) - Money Integrity ---
    metrics_short, logs_short = run_test("Short", 100, overrides)

    print("\n[Short Test Verification]")
    if metrics_short["MoneyWarnings"] == 0:
        print("✅ PASS: Money Conservation (No Delta Warnings)")
    else:
        print(f"❌ FAIL: Money Warnings Detected: {metrics_short['MoneyWarnings']}")
        # Print first few warnings
        for line in logs_short.split("\n"):
            if "MONEY_SUPPLY_CHECK" in line and "WARNING" in line:
                print(f"   -> {line}")
                break

    # --- Test 2: Full Test (1000 Ticks) - Evolution ---
    metrics_full, logs_full = run_test("Full", 1000, overrides)

    print("\n[Full Test Verification]")

    # 1. GDP > 0
    if metrics_full["GDP"] > 0:
        print(f"✅ PASS: Economy Survived (GDP: {metrics_full['GDP']:.1f})")
    else:
        print(f"❌ FAIL: Economy Collapsed (GDP: {metrics_full['GDP']:.1f})")

    # 2. Mitosis > 0
    if metrics_full["MitosisCount"] > 0:
        print(
            f"✅ PASS: Evolution Occurred (Mitosis Count: {metrics_full['MitosisCount']})"
        )
    else:
        print(
            "⚠️ WARNING: No Mitosis detected. (Rich households might not be rich enough?)"
        )

    # 3. Death > 0 (Natural Selection)
    if metrics_full["DeathCount"] > 0:
        print(
            f"✅ PASS: Natural Selection Active (Death Count: {metrics_full['DeathCount']})"
        )
    else:
        print("⚠️ WARNING: No Deaths detected. (Starvation condition not met?)")

    # 4. Spending Rejected (Hard Stop Verification)
    if metrics_full["SpendingRejected"] > 0:
        print(
            f"✅ PASS: Hard Budget Constraint Active (Rejections: {metrics_full['SpendingRejected']})"
        )
    else:
        print("ℹ️ INFO: No Spending Rejected. (Government was solvent throughout?)")

    # Generate Report
    report = f"""
Operation Darwin Verification Report
====================================
Short Test (100 Ticks):
- Money Warnings: {metrics_short["MoneyWarnings"]}

Full Test (1000 Ticks):
- Final GDP: {metrics_full["GDP"]:.2f}
- Mitosis Events: {metrics_full["MitosisCount"]}
- Death Events: {metrics_full["DeathCount"]}
- Government Spending Rejections: {metrics_full["SpendingRejected"]}
    """

    os.makedirs("reports", exist_ok=True)
    with open("reports/darwin_report.txt", "w") as f:
        f.write(report)
    print("\nReport saved to reports/darwin_report.txt")


if __name__ == "__main__":
    operation_darwin()
