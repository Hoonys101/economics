# MISSION SPEC: [Wave 6] Implement Progressive Taxation and Wage Scaling (Fiscal Masking)

## 🎯 Objective
Resolve "Fiscal Masking" where simplistic stimuli hide underlying structural economic imbalances. Replace "helicopter money" with productivity-indexed wage scaling and progressive taxation.

## 🛠️ Implementation Details

### 1. Welfare Service: Stimulus Refinement
Modify `modules/government/services/welfare_service.py`:
- **File**: [welfare_service.py](file:///c:/coding/economics/modules/government/services/welfare_service.py)
- **Change**: De-prioritize the raw `welfare_support_stimulus` trigger. Instead of a flat survival cost multiple, make it dynamic or targeted.
- **Goal**: Reduce the frequency of large-scale stimulus while maintaining the unemployment safety net.

### 2. HR Strategy: Productivity-Indexed Wages
Modify `simulation/decisions/firm/hr_strategy.py`:
- **File**: [hr_strategy.py](file:///c:/coding/economics/simulation/decisions/firm/hr_strategy.py)
- **Change**: When calculating wage offers or adjustments, explicitly factor in the `productivity_factor` and current `inflation` metrics.
- **Logic**: 
  - `New Wage = Target Wage * (1 + Productivity Gain) * (1 + Inflation Offset)`
  - Avoid static wage floors that require constant government offset.

### 3. Taxation System: Progressive Hardening
Modify `modules/government/taxation/system.py`:
- **File**: [system.py](file:///c:/coding/economics/modules/government/taxation/system.py)
- **Change**: Ensure the `PROGRESSIVE` mode uses dynamic brackets calculated via `FiscalPolicyManager`.
- **Note**: The `FLAT` mode priority fix (already implemented by assistant) must be preserved.

## 🧪 Verification Plan
1. **Unit Tests**:
   - `tests/unit/test_wave6_fiscal_masking.py` (Execute and verify logic).
2. **System Simulation**:
   - Run a 100-tick simulation.
   - Verify that `Total Stimulus Paid` is lower than before while `Real Wages` correlate with productivity growth.