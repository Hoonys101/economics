# Specification: Inheritance and State Synchronization Audit

## 1. Executive Summary
This document provides a two-part technical specification. First, it details the required implementation for transferring stock portfolios to the government during escheatment, resolving a gap in the `InheritanceManager` (related to TD-160). Second, it presents an audit of the `TickOrchestrator`'s state synchronization mechanism, analyzing a potential violation of the TD-192 protocol and providing a definitive recommendation based on architectural constraints.

## 2. Escheatment Portfolio Transfer (TD-160) Implementation

### 2.1. Problem
The current `InheritanceManager` correctly handles the escheatment (transfer to government) of cash and real estate when a deceased agent has no heirs. However, it fails to transfer the agent's stock portfolio, causing those assets to be permanently lost from the simulation and violating the zero-sum principle.

### 2.2. Proposed Solution
Following the existing pattern in `InheritanceManager` where asset transfers are handled directly before settlement, we will add logic to transfer the stock portfolio to the government within the `if not heirs:` block.

**File**: `simulation/systems/inheritance_manager.py`
**Method**: `process_death`

```python
# In InheritanceManager.process_death, within the 'if not heirs:' block

        if not heirs:
            # Escheatment (To Gov)
            if cash > 0:
                distribution_plan.append((government, cash, "escheatment_cash", "escheatment"))

            # Escheat remaining Assets
            # Portfolio Transfer is handled by SettlementSystem (Atomic).
            # -> This comment is incorrect. Following existing pattern for Real Estate.

            # =================== [START] PROPOSED IMPLEMENTATION ===================
            # Portfolio Escheatment (Stocks)
            remaining_holdings = deceased._econ_state.portfolio.holdings
            if remaining_holdings:
                # It is assumed the government agent has a portfolio object.
                gov_portfolio = government._econ_state.portfolio
                for firm_id, share in remaining_holdings.items():
                    # Add shares to government portfolio. Assumes a method like 'add' or direct manipulation.
                    # If Portfolio.add exists:
                    gov_portfolio.add(firm_id, share.quantity, share.acquisition_price)

                    # Create a transaction record for the auditable transfer.
                    # Price is 0.0 as this is a transfer of ownership, not a market sale.
                    tx = Transaction(
                        buyer_id=government.id,
                        seller_id=deceased.id,
                        item_id=f"stock_{firm_id}",
                        quantity=share.quantity,
                        price=0.0,
                        market_id="stock_market",
                        transaction_type="asset_transfer_escheatment",
                        time=current_tick,
                        metadata={"executed": True, "reason": "Escheatment due to no heirs"}
                    )
                    transactions.append(tx)

                # Clear the deceased's portfolio holdings to finalize the transfer
                deceased._econ_state.portfolio.holdings.clear()
            # =================== [END] PROPOSED IMPLEMENTATION ===================

            # Real Estate Transfer (Manual)
            for unit in deceased_units:
                 unit.owner_id = government.id
                 tx = Transaction(
                        buyer_id=government.id,
                        seller_id=deceased.id,
                        item_id=f"real_estate_{unit.id}",
                        quantity=1.0,
                        price=0.0,
                        market_id="real_estate_market",
                        transaction_type="asset_transfer",
                        time=current_tick,
                        metadata={"executed": True, "reason": "Escheatment due to no heirs"}
                     )
                 transactions.append(tx)

```

### 2.3. Risk & Impact Audit
- **Dependency**: This solution assumes the `Government` agent has a `_econ_state.portfolio` attribute of type `Portfolio`, consistent with other agents. If not, this attribute must be added. It also assumes the `Portfolio` class has a method to add shares (e.g., `add()`).
- **Atomicity**: This change continues the existing pattern of non-atomic asset transfers within `InheritanceManager`. While it makes the system consistent, it does not resolve the underlying architectural issue described in TD-160 where asset transfers are not handled by the `SettlementSystem`. This adds to the technical debt but contains the change locally.
- **Testing**: Unit tests for `InheritanceManager` must be updated to include a scenario where a deceased agent with a stock portfolio and no heirs dies. The test must assert that the government's portfolio contains the escheated shares and that the deceased's portfolio is empty.

## 3. Audit of TickOrchestrator State Synchronization (TD-192)

### 3.1. Finding
An audit of `simulation/orchestration/tick_orchestrator.py` was conducted to identify direct asset modifications that might violate the TD-192 "Hub-and-Spoke" state synchronization protocol. One such modification was found in the `_drain_and_sync_state` method:

```python
# simulation/orchestration/tick_orchestrator.py:L164
if sim_state.government and hasattr(sim_state.government, "process_monetary_transactions"):
    sim_state.government.process_monetary_transactions(sim_state.transactions)
```

This line triggers a state modification on the `government` object *during* the state draining process, which appears to contradict the principle that the drain function should only be responsible for transferring data between the transient `SimulationState` and the persistent `WorldState`.

### 3.2. Analysis and Recommendation
Despite appearances, this line of code is **not an error** but a **critical and intentional architectural constraint** implemented to resolve ticket **TD-177 (M2 Integrity)**.

- **Purpose**: The `process_monetary_transactions` call provides a structural guarantee for the integrity of the M2 money supply. It ensures that all monetary flows (e.g., taxes, transfers) are incrementally calculated and tracked by the government agent *as soon as they are recorded*.
- **Architectural Constraint**: The end-of-tick money supply verification logic (`_finalize_tick`) relies on this incremental calculation. It compares the final money supply against a baseline adjusted by the government's recorded monetary delta. Removing or deferring this call would break the verification logic and re-introduce the very money supply "leaks" and integrity bugs that TD-177 was created to fix.
- **Conclusion**: The identified code is a deliberate exception to the general TD-192 protocol. It represents a higher-order integrity requirement taking precedence over the protocol's structural purity.

**Recommendation: DO NOT REFACTOR.**

This line must be preserved and treated as a foundational element of the simulation's economic integrity model. No other unsanctioned direct asset modifications were found within the `TickOrchestrator`. All other state-syncing operations (`effects_queue.extend`, `inter_tick_queue.extend`, etc.) correctly follow the TD-192 protocol.
