# Insight Report: TD-Waterfall-Arch

## 1. Technical Debt: Misplaced Documentation
- **Issue**: `PROJECT_STATUS.md` was located in `design/1_governance/`, causing a "Context Vacuum" for agents expecting it at the root.
- **Impact**: AI agents and automated scripts failed to track project status accurately, leading to redundant checks or hallucinations.
- **Resolution**: Moved `PROJECT_STATUS.md` to the root directory and updated all references (`design/INDEX.md`, `scripts/checkpoint.py`, etc.).
- **Prevention**: Enforce root-level placement for "Single Source of Truth" documents (PROJECT_STATUS, CHANGELOG, etc.) in the project structure guidelines.

## 2. Architectural Insight: Liquidation Waterfall Protocol
- **Observation**: The "Liquidation Waterfall" (TD-187) is a critical component of the `SystemicLiquidation` phase. It prioritizes labor claims over capital claims, which is a significant deviation from "standard" capitalist models that might prioritize secured debt absolutely.
- **Significance**: This reflects a "Human-Centric" or "Social Market Economy" design choice. By capping severance at 3 years and wages at 3 months, it balances worker protection with creditor rights.
- **Risk**: The complexity of atomic distribution via `SettlementSystem` increases the risk of "Magic Money" leaks if floating-point errors occur during the split.
- **Action Item**: Ensure `LiquidationManager` uses strict integer math (or floor division with remainder handling) for all waterfall steps, similar to the `InheritanceManager` fix.

## 3. Metadata
- **Date**: 2026-02-03
- **Author**: Jules (via Antigravity)
- **Status**: **Registered**
