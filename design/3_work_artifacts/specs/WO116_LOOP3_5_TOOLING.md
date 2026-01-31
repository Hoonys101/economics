# MISSION: Loop 3.5 (Refine Verification Tool)

## 1. SITUATION
- We need a forensic tool to catch "Shadow Mutations" (direct asset changes without transactions).
- Huge leaks (-6 process 60k+) are occurring, but records are silent.

## 2. GOAL: Standardized Forensic Output
Modify `scripts/diagnose_money_leak.py` to produce the EXACT format below.

### Requirements:
1. **Silence Noise**: Suppress all `DEBUG` and `INFO` logs from other modules.
2. **Standard Format (Implement this strictly)**:
 ```text
 TICK: [N] | LEAK: [Value] | TOTAL_M2: [Value]
 [FORENSIC] Significant Leak Detected at Tick [N]
 Reconciliation Check:
 - System Asset Delta: [Sum of all agent.assets changes]
 - Money Supply Delta: [Issued - Destroyed]
 - Unexplained (Leak): [Asset Delta - Money Supply Delta]
 Transaction Summary:
 Type | Count | Volume
 --------------------------+----------+----------------
 [Type A] | [#] | [Total Amount]
 ```
3. **Internal Logic**:
 - Store total assets of ALL agents at the start of the tick.
 - At the end of the tick, compare with new total.
 - Collect ALL `Transaction` objects created during the tick (you may need to mock or hook into the `SettlementSystem` or `world_state.transactions_history`).
 - If `abs(Unexplained) > 1.0`, print the [FORENSIC] block.

## 3. DELIVERABLE
- Updated `scripts/diagnose_money_leak.py`.
- Final audit of Tick 1-10 results using this new format.
