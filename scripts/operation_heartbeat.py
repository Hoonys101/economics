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

# Configure Logger to silence standard info logs during 2000 ticks (too noisy)
logging.basicConfig(level=logging.WARNING)

def operation_heartbeat():
    print("🚀 Operation Heartbeat: Initiating Grand Simulation (2000 Ticks)...")
    
    # 1. Configuration Override
    overrides = {
        "SIMULATION_TICKS": 2000,
        "NUM_HOUSEHOLDS": 20, # Keep manageable
        "NUM_FIRMS": 5,
        "INITIAL_BASE_ANNUAL_RATE": 0.05,
    }
    
    # 2. Initialize Simulation
    sim = create_simulation(overrides=overrides)
    
    # 3. Execution Loop with Telemetry
    records = []
    print("❤️ Pulse check started...")
    
    metrics = {
        "prev_price": 10.0
    }

    try:
        for tick in range(1, 2001):
            sim.run_tick()
            
            # Telemetry Extraction
            indicators = sim.tracker.get_latest_indicators()
            current_price = indicators.get("avg_goods_price", 10.0)
            
            # Calculate Period Inflation
            inflation = 0.0
            if metrics["prev_price"] > 0:
                inflation = (current_price - metrics["prev_price"]) / metrics["prev_price"]
            metrics["prev_price"] = current_price
            
            # Household Savings Rate Estimate
            total_income = 0.0
            total_consumption = 0.0
            active_households = 0
            for h in sim.households:
                if h._bio_state.is_active:
                    total_income += h._econ_state.current_wage
                    total_consumption += h._econ_state.current_consumption
                    active_households += 1
            
            savings_rate = 0.0
            if total_income > 0:
                savings_rate = (total_income - total_consumption) / total_income
                
            record = {
                "Tick": tick,
                "BaseRate": sim.bank.base_rate,
                "GDP": indicators.get("total_production", 0),
                "AvgPrice": current_price,
                "Inflation": inflation,
                "ActiveFirms": len([f for f in sim.firms if f.is_active]),
                "ActiveHouseholds": active_households,
                "SavingsRate": savings_rate,
                "Unemployment": indicators.get("unemployment_rate", 0),
                "ApprovalRating": sim.government.average_approval_rating
            }
            records.append(record)
            
            if tick % 100 == 0:
                print(f"   Tick {tick}: GDP={record['GDP']:.1f}, Rate={record['BaseRate']:.2%}, Firms={record['ActiveFirms']}")
                
    except KeyboardInterrupt:
        print("\n⚠️ Simulation interrupted by user.")
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sim.repository.close()
        
    # 4. Export Report
    df = pd.DataFrame(records)
    output_path = "simulation_results/final_report.csv"
    os.makedirs("simulation_results", exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\n📄 Report saved to {output_path}")
    
    # 5. Automated Analysis
    analyze_results(df)

def analyze_results(df):
    print("\n🔍 DIAGNOSTIC REPORT")
    print("-" * 50)
    
    # A. The Pulse (Volatility)
    gdp = df["GDP"]
    gdp_std = gdp.std()
    gdp_mean = gdp.mean()
    cv = gdp_std / gdp_mean if gdp_mean > 0 else 0
    print(f"1. THE PULSE (Business Cycle)")
    print(f"   - GDP Volatility (CV): {cv:.2%} (Target: > 5%, < 50%)")
    if 0.05 < cv < 0.5:
        print("   ✅ PASS: Significant economic fluctuations detected.")
    else:
        print("   ⚠️ WARNING: Economy might be stagnant or chaotic.")

    # B. The Intervention (Correlation)
    # Check correlation between Rate and lagged Inflation?
    # Simple check: Does Rate change?
    rate_std = df["BaseRate"].std()
    print(f"\n2. THE INTERVENTION (Monetary Policy)")
    print(f"   - Rate Volatility: {rate_std:.4f}")
    if rate_std > 0.0001:
         print("   ✅ PASS: Central Bank is active.")
    else:
         print("   FAIL: Central Bank is asleep (Flat rate).")
         
    # Check Savings Response
    # Correlation between SavingsRate and Real Rate (Rate - Inflation)
    # df["RealRate"] = df["BaseRate"] - df["Inflation"] # Period inflation mismatch
    # Just check if SavingsRate varies
    savings_std = df["SavingsRate"].std()
    print(f"   - Savings Volatility: {savings_std:.4f}")
    
    # C. The Metabolism (Firms)
    firms_start = df["ActiveFirms"].iloc[0]
    firms_end = df["ActiveFirms"].iloc[-1]
    firms_min = df["ActiveFirms"].min()
    print(f"\n3. THE METABOLISM (Corporate Life)")
    print(f"   - Start: {firms_start}, End: {firms_end}, Min: {firms_min}")
    if firms_end != firms_start or firms_min < firms_start:
        print("   ✅ PASS: Dynamic entry/exit detected.")
    else:
        print("   ⚠️ WARNING: Corporate landscape is static.")

    print("-" * 50)
    print("End of Report.")

if __name__ == "__main__":
    operation_heartbeat()
