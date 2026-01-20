import sys
from pathlib import Path
import os
import pandas as pd
import numpy as np
import logging

# Setup paths to import project modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import create_simulation
import config

# Configure Logger to INFO level for higher visibility as requested
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def operation_trinity():
    print("[Operation Trinity]: Initiating Grand Adaptive Interaction Test (2000 Ticks)...")
    
    # 1. Configuration Override
    overrides = {
        "SIMULATION_TICKS": 2000,
        "NUM_HOUSEHOLDS": 20,
        "NUM_FIRMS": 10,  # Increased for corporate life cycle monitoring
        "INITIAL_BASE_ANNUAL_RATE": 0.05,
        "TAX_RATE_BASE": 0.10,
        "DEBT_CEILING_RATIO": 1.5, # Slightly higher as per Architect's Criteria
    }
    
    # 2. Initialize Simulation
    sim = create_simulation(overrides=overrides)
    
    # 3. Execution Loop with Enhanced Telemetry
    records = []
    print("Monitoring 3-Agent Adaptivity...")
    
    prev_metrics = {
        "prev_avg_price": 10.0
    }

    try:
        for tick in range(1, 2001):
            sim.run_tick()
            
            # Telemetry Extraction
            indicators = sim.tracker.get_latest_indicators()
            current_price = indicators.get("avg_goods_price", 10.0)
            
            # Inflation
            inflation = 0.0
            if prev_metrics["prev_avg_price"] > 0:
                inflation = (current_price - prev_metrics["prev_avg_price"]) / prev_metrics["prev_avg_price"]
            prev_metrics["prev_avg_price"] = current_price
            
            # Firm Metrics (Averaged)
            active_firms = [f for f in sim.firms if f.is_active]
            avg_marketing_rate = np.mean([f.marketing_budget_rate for f in active_firms]) if active_firms else 0
            total_revenue = sum([f.revenue_this_turn for f in active_firms])
            
            # Government Metrics
            gov = sim.government
            debt_ratio = gov.total_debt / max(gov.potential_gdp, 1.0)
            
            # Household Metrics
            active_households = [h for h in sim.households if h.is_active]
            # Fix: consumption_aggressiveness is internal state. Use current_consumption instead.
            avg_consumption = np.mean([h.current_consumption for h in active_households]) if active_households else 0
            
            record = {
                "Tick": tick,
                "GDP": indicators.get("total_production", 0),
                "CPI": current_price,
                "Inflation": inflation,
                "BaseRate": sim.bank.base_rate,
                "TaxRate": gov.effective_tax_rate,
                "DebtRatio": debt_ratio,
                "FiscalStance": gov.fiscal_stance,
                "ActiveFirms": len(active_firms),
                "AvgMarketingRate": avg_marketing_rate,
                "TotalRevenue": total_revenue,
                "AvgConsumption": avg_consumption,
                "Unemployment": indicators.get("unemployment_rate", 0),
                "ApprovalRating": gov.average_approval_rating
            }
            records.append(record)
            
            if tick % 100 == 0:
                print(f"   Tick {tick:4}: GDP={record['GDP']:5.1f} | Tax={record['TaxRate']:4.1%} | Debt/GDP={record['DebtRatio']:4.2f} | Firms={record['ActiveFirms']}")
                
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sim.repository.close()
        
    # 4. Export Report
    df = pd.DataFrame(records)
    output_path = "simulation_results/trinity_report.csv"
    os.makedirs("simulation_results", exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\nReport saved to {output_path}")
    
    # 5. Automated Analysis against Success Criteria
    analyze_trinity(df)

def analyze_trinity(df):
    print("\nDIAGNOSTIC REPORT: OPERATION TRINITY")
    print("=" * 60)
    
    # 1. Government (Counter-cyclicality)
    # Correlation between GDP Growth and TaxRate
    df['GDP_Growth'] = df['GDP'].pct_change()
    corr_gdp_tax = df['GDP_Growth'].corr(df['TaxRate'])
    print(f"1. GOVERNMENT ADAPTIVITY (Fiscal)")
    print(f"   - GDP-Tax Correlation: {corr_gdp_tax:.4f} (Expected Positive for Pro-cyclical, Negative/Zero for Counter-cyclical)")
    # Actually, if GDP growth is high, we want TaxRate to increase (Counter-cyclical) -> Positive Correlation
    # Wait, Stance = -OutputGap. OutputGap high -> Stance negative -> TaxRate = Base * (1 - Stance) = Base * (1 + |Stance|) -> TaxRate high.
    # So Positive Correlation is CORRECT for counter-cyclical tax policy.
    if corr_gdp_tax > 0.1:
        print("   ✅ PASS: Tax policy is counter-cyclical (Tax rises with growth).")
    else:
        print("   ⚠️ WARNING: Fiscal response might be weak or pro-cyclical.")

    # 2. Firm (Survival & Marketing)
    firms_start = df["ActiveFirms"].iloc[0]
    firms_end = df["ActiveFirms"].iloc[-1]
    bankruptcy_rate = (firms_start - firms_end) / firms_start if firms_start > 0 else 0
    print(f"\n2. FIRM ADAPTIVITY (Marketing & Survival)")
    print(f"   - Bankruptcy Rate: {bankruptcy_rate:.1%} (Threshold: < 30%)")
    if bankruptcy_rate < 0.3:
        print("   ✅ PASS: Corporate ecosystem is stable.")
    else:
        print("   ❌ FAIL: Mass extinction detected.")
        
    # Marketing ROI Correlation (Revenue vs MarketingRate)
    corr_rev_mkt = df['TotalRevenue'].corr(df['AvgMarketingRate'])
    print(f"   - Revenue-Marketing Correlation: {corr_rev_mkt:.4f}")
    if corr_rev_mkt > 0.2:
        print("   ✅ PASS: Marketing spend is responsive to revenue.")

    # 3. System Stability
    max_debt = df["DebtRatio"].max()
    print(f"\n3. SYSTEM STABILITY")
    print(f"   - Max Debt/GDP Ratio: {max_debt:.2f} (Threshold: < 1.5)")
    if max_debt < 1.5:
        print("   ✅ PASS: Fiscal sustainability maintained.")
    else:
        print("   ❌ FAIL: Debt explosion detected.")

    last_inflation = df["Inflation"].tail(100).mean()
    print(f"   - Last 100-Tick Avg Inflation: {last_inflation:.2%}")
    if -0.1 < last_inflation < 0.1:
        print("   ✅ PASS: Price stability maintained (no hyper-fluctuation).")
    else:
        print("   ⚠️ WARNING: Inflation is drifting outside healthy bounds.")

    print("=" * 60)
    print("End of Trinity Diagnostic.")

if __name__ == "__main__":
    operation_trinity()
