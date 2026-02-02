
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

    initial_assets = {}
    for agent_id, agent in sim.agents.items():
        if hasattr(agent, "assets"):
            initial_assets[agent_id] = agent.assets

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

    # --- JULES UPDATE: Account for Fiscal Activities (Infrastructure / Bond Sales) ---
    # Scan transactions for Central Bank bond purchases (Money Creation)
    # Scan transactions for Infrastructure Spending (Diagnostic)

    cb_bond_buys = 0.0
    infra_spending = 0.0

    cb_id = sim.central_bank.id if sim.central_bank else None

    if hasattr(sim.world_state, "transactions"):
        for tx in sim.world_state.transactions:
            # Check if tx is object or dict
            if isinstance(tx, dict):
                 t_type = tx.get("transaction_type")
                 t_buyer = tx.get("buyer_id")
                 t_price = tx.get("price", 0.0)
                 t_qty = tx.get("quantity", 0.0)
            else:
                 t_type = getattr(tx, "transaction_type", None)
                 t_buyer = getattr(tx, "buyer_id", None)
                 t_price = getattr(tx, "price", 0.0)
                 t_qty = getattr(tx, "quantity", 0.0)

            # Bond Purchase by Central Bank (Credit Creation)
            if t_type == "bond_purchase" and str(t_buyer) == str(cb_id):
                cb_bond_buys += t_price

            # Infrastructure Spending (Transfer, but useful diagnostic)
            if t_type == "infrastructure_spending":
                infra_spending += (t_price * t_qty)

    if cb_bond_buys > 0:
        print(f"Detected Untracked CB Bond Purchases: {cb_bond_buys:,.2f}")
        authorized_delta += cb_bond_buys

    if infra_spending > 0:
        print(f"Detected Infrastructure Spending: {infra_spending:,.2f}")

    print(f"\nTick 1 (END) Total Money: {current_money:,.2f}")
    print(f"Baseline: {baseline_money:,.2f}")
    print(f"Authorized Delta (Minted - Destroyed + Credit): {authorized_delta:,.2f}")
    print(f"Actual Delta: {delta:,.2f}")

    # Inspect Individual Deltas
    print("\n--- Agent Asset Deltas ---")
    deltas = []
    for agent_id, agent in sim.agents.items():
        if hasattr(agent, "assets") and agent_id in initial_assets:
            d = agent.assets - initial_assets[agent_id]
            if abs(d) > 0.01:
                deltas.append((agent_id, d, type(agent).__name__))
    
    deltas.sort(key=lambda x: x[1], reverse=True)
    for aid, d, atype in deltas[:10]:
        print(f"{atype} {aid}: {d:,.2f}")
    if len(deltas) > 10:
        print("...")
        for aid, d, atype in deltas[-5:]:
             print(f"{atype} {aid}: {d:,.2f}")

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
