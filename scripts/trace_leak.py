
import logging
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from main import create_simulation

def trace():
    print("--- TRACE START ---")
    sim = create_simulation()
    
    print(f"Tick 0 (START) Total Money: {sim.world_state.calculate_total_money():,.2f}")
    
    # Baseline is established at Tick 0
    baseline_money = sim.world_state.calculate_total_money()

    for f in sim.world_state.firms:
        print(f"Firm {f.id}: Assets={f.assets:,.2f}, Active={f.is_active}")
    
    # --- WO-024: Manual Loan Grant for Verification ---
    target_firm = next((f for f in sim.world_state.firms if f.is_active), None)
    if target_firm:
        loan_amount = 5000.0
        interest_rate = 0.05

        grant_result = sim.bank.grant_loan(
            borrower_id=str(target_firm.id),
            amount=loan_amount,
            interest_rate=interest_rate
        )

        if grant_result:
            _loan_info, credit_tx = grant_result
            if credit_tx:
                sim.government.process_monetary_transactions([credit_tx])
                print(f"Loan granted to Firm {target_firm.id} for {loan_amount:,.2f}. Credit TX processed.")

    sim.run_tick()
    
    current_money = sim.world_state.calculate_total_money()
    delta = current_money - baseline_money
    
    # WO-120: Authorized Delta (Credit Creation / Destruction)
    authorized_delta = 0.0
    if hasattr(sim.government, "get_monetary_delta"):
        authorized_delta = sim.government.get_monetary_delta()

    # Add manual delta from pre-tick loan grant (which was reset in run_tick)
    if 'grant_result' in locals() and grant_result:
        authorized_delta += loan_amount

    print(f"\nTick 1 (END) Total Money: {current_money:,.2f}")
    print(f"Baseline: {baseline_money:,.2f}")
    print(f"Authorized Delta (Minted - Destroyed + Credit): {authorized_delta:,.2f}")
    print(f"Actual Delta: {delta:,.2f}")
    
    # Check Integrity
    leak = delta - authorized_delta
    if abs(leak) > 1.0:
        print(f"❌ LEAK DETECTED: {leak:,.4f}")
        sys.exit(1)
    else:
        print(f"✅ INTEGRITY CONFIRMED (Leak: {leak:,.4f})")

    for f in sim.world_state.firms:
        print(f"Firm {f.id}: Assets={f.assets:,.2f}, Active={f.is_active}")
        
    # Check if any firm was removed from the list
    all_agent_ids = [a.id for a in sim.world_state.get_all_agents()]
    print(f"\nAll Active Agent IDs: {all_agent_ids}")

if __name__ == "__main__":
    trace()
