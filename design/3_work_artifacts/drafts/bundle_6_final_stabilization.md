# Mission Guide: Phase 6 Final Stabilization (PH6_BASELINE_STABILIZATION)

## 1. Goal
Finalize the Phase 6 baseline by resolving the residual monetary leak, hardening the engine against multi-currency crashes, and integrating local persistence.

## 2. Technical Tasks

### A. Resolve Residual Leak (-71,328.04)
The simulation currently fails integrity assertions at Tick 1 with a variance of approximately **-71,328.04**.
- **Requirement**: Trace the flow of funds in `FinanceDepartment` and `TaxationSystem` to ensure every transaction that moves money between "M2 Holders" (HH, Firms, Gov) and "Non-M2 Holders" (Bank Reserves, System) is correctly logged in `MonetaryLedger`.
- **Target**: Zero leak (0.0000) or explanation of irreducible float noise (< 0.001).

### B. Engine Hardening (Multi-Currency Reset)
- **File**: `simulation/orchestration/phases/post_sequence.py`
- **Issue**: Lines 117-118 reset `expenses_this_tick` to `0.0`.
- **Requirement**: Standardize the reset to maintain the `Dict[CurrencyCode, float]` structure, or ensure `last_daily_expenses` correctly aggregates all currency values (converted) before the reset.

### C. Persistence Integration
- **File**: `simulation/orchestration/dashboard_service.py`
- **Requirement**: 
    1. Import `PersistenceBridge`.
    2. Initialize `self.persistence = PersistenceBridge()` in `__init__`.
    3. Call `self.persistence.save_snapshot(snapshot)` at the end of `get_snapshot()`.
    4. Ensure snapshots exist in `reports/snapshots/`.

## 3. Verification
Run `python scenarios/scenario_stress_100.py`. 
- **Success Criteria**: 100 ticks complete with 0.0000 leak and persistence reports generated.

## 4. Conditional Fallback (IMPORTANT)
If you find that the root cause of the -71k leak or the multi-currency crash is too deep or structurally complex to fix safely:
- **Prioritize Investigation**: Identify the exact files, lines, and logical flow responsible for the issue.
- **Detailed Report**: Document your findings in 'communications/insights/PH6_STABILIZATION_REPORT.md' and request architectural guidance instead of applying an incomplete or risky patch.

🚨 [MANDATORY] 작업 완료 전, 발견된 기술 부채와 인사이트를 'communications/insights/PH6_STABILIZATION_REPORT.md' 파일에 반드시 기록하십시오.
