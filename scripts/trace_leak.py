
import logging
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from main import create_simulation
from modules.system.api import DEFAULT_CURRENCY

def trace():
    print("--- TRACE START ---")
    sim = create_simulation()
    
    # Baseline (Pennies)
    baseline_money_pennies = sim.world_state.get_total_system_money_for_diagnostics()
    print(f"Tick 0 (START) Total Money ({DEFAULT_CURRENCY}): {baseline_money_pennies / 100.0:,.2f}")
    
    initial_balances = {}
    for agent_id, agent in sim.agents.items():
        if hasattr(agent, "balance_pennies"):
            initial_balances[agent_id] = agent.balance_pennies
        elif hasattr(agent, "get_balance"):
            initial_balances[agent_id] = agent.get_balance(DEFAULT_CURRENCY)
        else:
             # Fallback
             initial_balances[agent_id] = 0

    for f in sim.world_state.firms:
        print(f"Firm {f.id}: Assets={f.balance_pennies / 100.0:,.2f}, Active={f.is_active}")
    
    # --- WO-024: Manual Loan Grant for Verification ---
    target_firm = next((f for f in sim.world_state.firms if f.is_active), None)
    grant_result = None
    loan_amount_pennies = 500000 # 5000.00

    if target_firm:
        interest_rate = 0.05

        # Ensure we pass int
        grant_result = sim.bank.grant_loan(
            borrower_id=target_firm, # Pass object for SettlementSystem resolution
            amount=loan_amount_pennies,
            interest_rate=interest_rate
        )

        if grant_result:
            _loan_info, credit_tx = grant_result
            if credit_tx:
                sim.government.process_monetary_transactions([credit_tx])
                print(f"Loan granted to Firm {target_firm.id} for {loan_amount_pennies / 100.0:,.2f}. Credit TX processed.")

    # Monkey patch to retain transactions
    sim.retained_transactions = []
    original_finalize = sim.tick_orchestrator._finalize_tick
    def patched_finalize(sim_state):
        sim.retained_transactions = list(sim.world_state.transactions)
        original_finalize(sim_state)
    sim.tick_orchestrator._finalize_tick = patched_finalize

    sim.run_tick()
    
    current_money_pennies = sim.world_state.get_total_system_money_for_diagnostics()
    delta_pennies = current_money_pennies - baseline_money_pennies
    
    # WO-120: Authorized Delta (Credit Creation / Destruction)
    authorized_delta_pennies = 0.0
    if hasattr(sim.government, "get_monetary_delta"):
        # get_monetary_delta returns float pennies (from MonetaryLedger)
        authorized_delta_pennies = sim.government.get_monetary_delta(DEFAULT_CURRENCY)
    
    # Add manual delta from pre-tick loan grant (which was reset in run_tick)
    # The loan grant happened *before* run_tick, but the ledger reset happens at start of run_tick (in gov/ledger).
    # Wait, `sim.run_tick` -> `sim.tick_orchestrator.run_tick`?
    # Usually `Government.reset_tick_flow` is called.
    # If `credit_tx` was processed *before* run_tick, and ledger was reset *during* run_tick,
    # then `get_monetary_delta` (which tracks `this_tick`) might not include the pre-tick loan?
    # `MonetaryLedger.reset_tick_flow` clears `credit_delta_this_tick` but snapshots `total_money_issued`.
    # `get_monetary_delta` uses `total_money_issued - start_tick_money_issued`.
    # If `grant_loan` updated `total_money_issued` *before* `reset_tick_flow` (which snapshots `total` to `start`),
    # then the delta will be 0 for that loan in *this* tick's calculation.
    # SO we DO need to add manual delta if it wasn't captured in the tick's delta.

    # Actually, `sim.run_tick` calls `orchestrator.run_tick`.
    # If `Government` resets at start of tick.
    # The pre-tick loan updated `total_money_issued`.
    # Then `reset_tick_flow` sets `start_tick = total`.
    # So `delta` for the tick will NOT include the pre-tick loan.
    # BUT `baseline_money` was measured *before* the loan?
    # No, `baseline_money` measured at Start.
    # `grant_loan` happens. Money (Deposits) increases.
    # `run_tick` happens.
    # `current_money` measured.
    # Delta = Current - Baseline.
    # This Delta INCLUDES the loan.
    # Authorized Delta (from Ledger for *this tick*) excludes the loan (since it happened before snapshot reset).
    # So we MUST add `loan_amount` to `authorized_delta` to explain the difference.

    if grant_result:
        authorized_delta_pennies += loan_amount_pennies

    # --- JULES UPDATE: Account for Fiscal Activities (Infrastructure / Bond Sales / Interest) ---
    cb_bond_buys = 0.0
    comm_bank_bond_buys = 0.0
    deposit_interest = 0.0
    loan_interest = 0.0
    infra_spending = 0.0

    cb_id = sim.central_bank.id if sim.central_bank else None
    comm_bank_id = sim.bank.id if sim.bank else None

    transactions_to_check = getattr(sim, "retained_transactions", [])
    if not transactions_to_check and hasattr(sim.world_state, "transactions"):
        transactions_to_check = sim.world_state.transactions

    if transactions_to_check:
        print(f"DEBUG: Found {len(transactions_to_check)} transactions.")
        for tx in transactions_to_check:
            # Check if tx is object or dict
            if isinstance(tx, dict):
                 t_type = tx.get("transaction_type")
                 t_buyer = tx.get("buyer_id")
                 t_price = tx.get("price", 0.0)
                 t_qty = tx.get("quantity", 0.0)
            else:
                 t_type = getattr(tx, "transaction_type", None)
                 t_buyer = getattr(tx, "buyer_id", None)
                 t_seller = getattr(tx, "seller_id", None)
                 t_price = getattr(tx, "price", 0.0)
                 t_qty = getattr(tx, "quantity", 0.0)

            tx_val = t_price * t_qty # Pennies

            # DEBUG
            if isinstance(tx, dict):
                t_seller = tx.get("seller_id")

            # print(f"DEBUG TX: {t_type} | Buyer: {t_buyer} | Seller: {t_seller} | Val: {tx_val:.2f}")

            # Bond Purchase (Creation if by Bank or CB)
            if t_type == "bond_purchase":
                if str(t_buyer) == str(cb_id):
                    cb_bond_buys += tx_val
                elif str(t_buyer) == str(comm_bank_id):
                    comm_bank_bond_buys += tx_val

            # Interest
            if t_type == "deposit_interest":
                deposit_interest += tx_val
            elif t_type == "loan_interest":
                loan_interest += tx_val

            # Infrastructure Spending (Transfer, but useful diagnostic)
            if t_type == "infrastructure_spending":
                infra_spending += tx_val

    if cb_bond_buys > 0:
        print(f"Detected Untracked CB Bond Purchases (Should be in Ledger): {cb_bond_buys / 100.0:,.2f}")
        # CB Bond purchase creates money (Reserves). If not in Ledger, add here.
        # Usually handled by MonetaryLedger if event triggered.
        # But if strictly tracing leakage vs authorized.
        # Assuming Ledger tracks it. If leakage detected, we can inspect.
        pass

    if comm_bank_bond_buys > 0:
        print(f"Detected Commercial Bank Bond Purchases (M2 Creation) (Should be in Ledger): {comm_bank_bond_buys / 100.0:,.2f}")
        pass

    if deposit_interest > 0:
        print(f"Detected Deposit Interest (M2 Creation) (Should be in Ledger): {deposit_interest / 100.0:,.2f}")
        pass

    if loan_interest > 0:
        print(f"Detected Loan Interest (M2 Destruction) (Should be in Ledger): {loan_interest / 100.0:,.2f}")
        pass

    if infra_spending > 0:
        print(f"Detected Infrastructure Spending: {infra_spending / 100.0:,.2f}")

    print(f"\nTick 1 (END) Total Money: {current_money_pennies / 100.0:,.2f}")
    print(f"Baseline: {baseline_money_pennies / 100.0:,.2f}")
    print(f"Authorized Delta (Minted - Destroyed + Credit): {authorized_delta_pennies / 100.0:,.2f}")
    print(f"Actual Delta: {delta_pennies / 100.0:,.2f}")

    # Inspect Individual Deltas
    print("\n--- Agent Asset Deltas (Dollars) ---")
    deltas = []
    for agent_id, agent in sim.agents.items():
        if agent_id in initial_balances:
            curr_balance = 0
            if hasattr(agent, "balance_pennies"):
                curr_balance = agent.balance_pennies
            elif hasattr(agent, "get_balance"):
                curr_balance = agent.get_balance(DEFAULT_CURRENCY)

            d = curr_balance - initial_balances[agent_id]
            if abs(d) > 1: # > 1 penny
                deltas.append((agent_id, d, type(agent).__name__))
    
    deltas.sort(key=lambda x: x[1], reverse=True)
    for aid, d, atype in deltas[:10]:
        print(f"{atype} {aid}: {d / 100.0:,.2f}")
    if len(deltas) > 10:
        print("...")
        for aid, d, atype in deltas[-5:]:
             print(f"{atype} {aid}: {d / 100.0:,.2f}")

    # Check Integrity
    leak_pennies = delta_pennies - authorized_delta_pennies
    if abs(leak_pennies) > 100: # Allow 1 dollar drift for float precision if any, but should be 0 with int
        print(f"❌ LEAK DETECTED: {leak_pennies / 100.0:,.4f}")
        sys.exit(1)
    else:
        print(f"✅ INTEGRITY CONFIRMED (Leak: {leak_pennies / 100.0:,.4f})")

    for f in sim.world_state.firms:
        print(f"Firm {f.id}: Assets={f.balance_pennies / 100.0:,.2f}, Active={f.is_active}")
        
    # Check if any firm was removed from the list
    all_agent_ids = [a.id for a in sim.world_state.get_all_agents()]
    print(f"\nAll Active Agent IDs: {len(all_agent_ids)}")

if __name__ == "__main__":
    try:
        trace()
    except Exception as e:
        import traceback
        print("\n--- CRASH DIAGNOSTIC ---")
        traceback.print_exc()
        sys.exit(1)
