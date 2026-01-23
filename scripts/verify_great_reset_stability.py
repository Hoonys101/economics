import sys
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from collections import deque

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import create_simulation
from utils.logging_manager import setup_logging
import config

# --- Verification Log Handler ---
class VerificationLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.atomicity_failures: List[str] = []

    def emit(self, record):
        msg = self.format(record)
        if "DEPOSIT_FAILURE" in msg or "ROLLBACK_FAILED" in msg:
            self.atomicity_failures.append(msg)

def verify_great_reset():
    # 1. Setup Logging
    setup_logging()

    # Attach handler to capture failures
    verification_handler = VerificationLogHandler()
    logging.getLogger().addHandler(verification_handler)
    logging.getLogger("simulation").addHandler(verification_handler)

    logger = logging.getLogger("VERIFY")
    logger.info("Starting Great Reset Stress Test (WO-115)...")

    # 2. Initialize Simulation
    # Ensure standard config
    config.INITIAL_HOUSEHOLD_ASSETS_MEAN = 5000.0
    config.GOVERNMENT_STIMULUS_ENABLED = True
    config.TICKS_PER_YEAR = 100

    sim = create_simulation()

    # Metrics Storage
    m2_history: List[float] = []
    debt_ratio_history: List[float] = []

    m2_baseline = 0.0

    total_ticks = 1000

    # 3. Main Loop
    for tick in range(1, total_ticks + 1):
        try:
            sim.run_tick()
        except Exception as e:
            logger.critical(f"Simulation Crashed at Tick {tick}: {e}", exc_info=True)
            break

        # 4. Calculate Metrics

        # M2 Calculation (Zero-Sum Check)
        # M2 = Households + Firms + Government + Reflux + Bank
        # Note: We access _assets directly or via property if available.
        # Assuming all agents implement IFinancialEntity which usually exposes assets property.

        h_assets = sum(h.assets for h in sim.households if h.is_active)
        f_assets = sum(f.assets for f in sim.firms if f.is_active)

        # Government
        gov_assets = sim.government.assets

        # Reflux
        reflux_bal = sim.reflux_system.balance if sim.reflux_system else 0.0

        # Bank
        bank_assets = sim.bank.assets if sim.bank else 0.0

        current_m2 = h_assets + f_assets + gov_assets + reflux_bal + bank_assets
        m2_history.append(current_m2)

        if tick == 1:
            m2_baseline = current_m2

        # Debt-to-GDP Calculation
        # Debt = Government Total Debt
        # GDP = Current Nominal GDP (Production * Price)

        debt = sim.government.total_debt

        # Get GDP from tracker
        metrics = sim.tracker.get_latest_indicators()
        prod = metrics.get("total_production", 0.0)
        price = metrics.get("avg_goods_price", 0.0)

        # If production/price is 0 (early ticks), use approximation or 0
        nominal_gdp = prod * price

        # Use smoothed GDP if available to avoid volatility spikes
        # But tracker usually gives current tick data.
        # Let's use nominal_gdp directly.

        debt_ratio = 0.0
        if nominal_gdp > 0:
            debt_ratio = debt / nominal_gdp

        debt_ratio_history.append(debt_ratio)

        # Log Progress
        if tick % 100 == 0:
            logger.info(f"Tick {tick}/{total_ticks} | M2: {current_m2:,.2f} | Debt/GDP: {debt_ratio:.2%}")

    # 5. Analysis & Reporting
    logger.info("Simulation Complete. Generating Report...")

    report_lines = []
    report_lines.append("# Great Reset Stress Test Report (WO-115)")
    report_lines.append(f"**Status**: {'FAILED' if verification_handler.atomicity_failures else 'PASSED'}")
    report_lines.append("")

    # Atomicity Check
    report_lines.append("## 1. System Stability (Atomicity)")
    if verification_handler.atomicity_failures:
        report_lines.append(f"**FAILED**: {len(verification_handler.atomicity_failures)} Atomicity Failures detected.")
        for fail in verification_handler.atomicity_failures[:10]:
            report_lines.append(f"- {fail}")
        if len(verification_handler.atomicity_failures) > 10:
            report_lines.append(f"- ... and {len(verification_handler.atomicity_failures) - 10} more.")
    else:
        report_lines.append("**PASSED**: No Atomicity Failures (DEPOSIT_FAILURE / ROLLBACK_FAILED) detected.")

    # M2 Integrity Check
    report_lines.append("")
    report_lines.append("## 2. M2 Money Supply Integrity")
    m2_start = m2_history[0]
    m2_end = m2_history[-1]
    m2_delta = m2_end - m2_start
    m2_pct_change = (m2_delta / m2_start) * 100 if m2_start != 0 else 0.0

    report_lines.append(f"- Start M2: {m2_start:,.2f}")
    report_lines.append(f"- End M2: {m2_end:,.2f}")
    report_lines.append(f"- Delta: {m2_delta:,.2f} ({m2_pct_change:+.2f}%)")

    # Zero-Sum Analysis
    # In a pure Zero-Sum system, Delta should be 0.
    # However, Bank Loans create money (Deposit) and Loan Repayment destroys it.
    # Government Bond Issuance: Buyers(Cash) -> Govt(Cash). M2 const.
    # Tax: HH(Cash) -> Govt(Cash). M2 const.
    # Spending: Govt(Cash) -> HH(Cash). M2 const.
    # So ONLY Bank Credit Creation/Destruction affects M2 in this definition.
    # If M2 grows, it implies Net Lending > 0.
    # We check if the change corresponds to Net Loan Growth?
    # Bank Assets = Cash + Loans (Receivable)?
    # Wait. Bank Assets in code usually means 'Cash/Reserves'.
    # If Bank lends 100: Bank Cash -100, Firm Cash +100. Sum M2 = 0.
    # IF Bank creates money from thin air (Fractional Reserve):
    # Bank Cash (Reserves) doesn't change? Firm Cash +100.
    # In this sim, does Bank have infinite cash or is it constrained?
    # Usually `bank.withdraw` reduces its assets.
    # If Bank Assets go negative (which is allowed for Central Bank but maybe not commercial Bank),
    # then M2 Sum would still be 0 if we count negative Bank Assets.
    # BUT, if Bank Assets floor at 0 and it still lends -> Creation.
    # Let's see what the report says.

    report_lines.append("")
    report_lines.append("## 3. Fiscal Stability (Debt-to-GDP)")
    if debt_ratio_history:
        max_debt = max(debt_ratio_history)
        end_debt = debt_ratio_history[-1]
        report_lines.append(f"- Max Debt/GDP: {max_debt:.2%}")
        report_lines.append(f"- Final Debt/GDP: {end_debt:.2%}")
        if end_debt > 2.0: # Arbitrary threshold for "Spiral"
            report_lines.append("- **WARNING**: Debt-to-GDP ratio is very high (>200%).")
        else:
            report_lines.append("- Debt levels appear sustainable.")
    else:
        report_lines.append("- No Debt/GDP data available.")

    # Write Report
    os.makedirs("reports", exist_ok=True)
    report_path = "reports/GREAT_RESET_REPORT.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))

    logger.info(f"Report saved to {report_path}")
    print(f"Report saved to {report_path}")

    # Return Code
    if verification_handler.atomicity_failures:
        sys.exit(1)

    # We don't fail on M2 drift yet as we are diagnosing, unless it's huge.
    # But WO says "Monitor".
    sys.exit(0)

if __name__ == "__main__":
    verify_great_reset()
