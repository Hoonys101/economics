import sys
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

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

def verify_great_reset_stability():
    """
    WO-115: Great Reset Stability Verification
    Runs 1,000 ticks and monitors M2 Money Supply and Debt-to-GDP.
    Enforces Zero-Sum Integrity.
    """
    # 1. Setup Logging
    setup_logging()
    verification_handler = VerificationLogHandler()
    logging.getLogger().addHandler(verification_handler)
    
    logger = logging.getLogger("VERIFY")
    logger.info("Starting Great Reset Stability Verification (WO-115)...")

    # 2. Initialize Simulation
    # Ensure stable parameters for stress test
    config.TICKS_PER_YEAR = 100
    config.GOVERNMENT_STIMULUS_ENABLED = True
    
    sim = create_simulation()
    
    # Baseline M2 (Zero-Sum start)
    # M2 Definition: Sum of all agent assets + bank reserves
    def get_total_m2():
        h_assets = sum(h._econ_state.assets for h in sim.households if h._bio_state.is_active)
        f_assets = sum(f.assets for f in sim.firms if f.is_active)
        gov_assets = sim.government.assets
        bank_assets = sim.bank.assets
        
        return h_assets + f_assets + gov_assets + bank_assets

    m2_start = get_total_m2()
    logger.info(f"Initial M2: {m2_start:,.2f}")

    drift_history = []
    total_ticks = 1000

    # 3. Execution Loop
    for tick in range(1, total_ticks + 1):
        try:
            sim.run_tick()
        except Exception as e:
            logger.critical(f"Simulation CRASHED at tick {tick}: {e}")
            break
            
        # Monitor Drift
        current_m2 = get_total_m2()
        drift = current_m2 - m2_start
        drift_history.append(drift)
        
        if tick % 100 == 0:
            debt_to_gdp = sim.government.get_debt_to_gdp_ratio()
            logger.info(f"Tick {tick:4} | M2: {current_m2:,.2f} | Drift: {drift:+.4f} | Debt/GDP: {debt_to_gdp:.2%}")

    # 4. Final Analysis
    logger.info("Simulation Complete. Finalizing Report.")
    
    m2_end = get_total_m2()
    total_drift = m2_end - m2_start
    
    report = []
    report.append("# Great Reset Stability Report")
    report.append(f"**Final Status**: {'PASSED' if abs(total_drift) < 1.0 else 'FAILED'}")
    report.append("")
    report.append(f"- **Start M2**: {m2_start:,.2f}")
    report.append(f"- **End M2**: {m2_end:,.2f}")
    report.append(f"- **Total Drift**: {total_drift:+.4f}")
    report.append(f"- **Max Drift**: {max(drift_history, key=abs):+.4f}")
    report.append("")
    report.append("## Atomicity Integrity")
    if verification_handler.atomicity_failures:
        report.append(f"**FAILED**: {len(verification_handler.atomicity_failures)} failures detected.")
        for f in verification_handler.atomicity_failures[:5]:
            report.append(f"- {f}")
    else:
        report.append("**PASSED**: No atomicity failures.")

    os.makedirs("reports", exist_ok=True)
    with open("reports/GREAT_RESET_REPORT.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    logger.info("Report saved to reports/GREAT_RESET_REPORT.md")
    
    if abs(total_drift) >= 1.0:
        logger.error(f"CRITICAL: M2 Money Supply Drift detected! Total Leak: {total_drift:.4f}")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    verify_great_reset_stability()
