# MISSION: Track A - Finance & Economic Integrity Audit
# Role: Jules (Economic Auditor)

## Objective
Verify and enforce Zero-Sum integrity across all financial transactions. Eliminate float incursions and align the SettlementSystem with the strict integer penny standard.

## Scope
- `simulation/systems/settlement_system.py`
- `simulation/systems/handlers/monetary_handler.py`
- `simulation/systems/handlers/goods_handler.py`
- `audits/audit_economic_integrity.py`

## Specific Tasks
1. **Integer Enforcement**: Audit all transaction handlers to ensure `total_pennies` is the sole source of truth (SSoT). Raise `FloatIncursionError` if any float price/amount is used in settlement.
2. **Taxation Atomicity**: Verify that Sales Tax is collected in the same atomic block as the trade.
3. **M2 Validation**: Implement `audit_total_m2` check at the end of each tick in `TickOrchestrator`.
4. **Forensics**: Log `MONEY_SUPPLY_CHECK` tags for every expansion/contraction (Bond issuance, OMO, LLR).

## Success Criteria
- `pytest tests/finance/` passes with 100% coverage.
- `EconomicIntegrityAudit` returns ZERO leaks over a 100-tick stress run.
