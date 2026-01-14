# Reliability Calibration Ledger

This file tracks the reliability of `gemini-cli` workers across different categories.
Promotion requires 3 consecutive successes (Calibration Mode) to Reach Level 2, and then 3 consecutive successes (Review Mode) to reach Level 3.

## Summary Status

| Category (Worker + Manual) | Current Level | Calibration Progress | Review Progress | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Reporter** (`reporter.md`) | **Level 2** | ✅ 3/3 | ⬜ 1/3 | Review Mode |
| **Spec Drafter** (`spec_writer.md`) | **Level 2** | ✅ 3/3 | ⬜ 2/3 | Review Mode |
| **Validator** (`validator.md`) | **Level 2** | ✅ 3/3 | ⬜ 0/3 | Review Mode |
| **State Auditor** (`state_auditor.md`) | **Level 2** | ✅ 3/3 | ⬜ 0/3 | Review Mode |
| **Context Manager** (`context_manager.md`) | **Level 1** | ⬜ 2/3 | ⬜ 0/3 | Calibration Mode |
| **Git Operator** (`git_operator.md`) | **Level 2** | ✅ 3/3 | ⬜ 0/3 | Review Mode |
| **Code Auditor** (`code_auditor.md`) | **Level 1** | ✅ 1/3 | ⬜ 0/3 | Calibration Mode | ✨ NEW |
| **Sync Verifier** (`sync_verifier.md`) | **Level 1** | ⬜ 0/3 | ⬜ 0/3 | Calibration Mode | ✨ NEW |

---

## 📅 Calibration History

### [Category: Reporter]
... (lines 24-30 remains)
4. ✅ **Case 4: WO-058 Crash & Glut Diagnosis** (2026-01-14)
   - Result: PASS. Correctly identified ZeroDivisionError and Inventory Glut mechanism.

### [Category: Spec Drafter]
... (lines 33-39 remains)
4. ✅ **Case 4: WO-056/058 Stabilization Spec** (2026-01-14)
   - Result: PASS. High-quality protocols and API definitions.
5. ✅ **Case 5: AssetLiquiditySystem Spec (v2)** (2026-01-14)
   - Result: PASS. Comprehensive waterfall and haircut logic.

### [Category: Validator]
... (lines 42-48 remains)

### [Category: State Auditor]
... (lines 51-57 remains)

### [Category: Context Manager]
... (lines 60-64 remains)

### [Category: Git Operator]
1. ✅ **Case 1: Calibration Commits** (2026-01-14)
   - Result: PASS.
2. ✅ **Case 2: Final Push Push** (2026-01-14)
   - Result: PASS.
3. ✅ **Case 3: Spec Promotion (mv commands)** (2026-01-14)
   - Result: PASS.
   - **PROMOTED TO LEVEL 2**

### [Category: Code Auditor]
1. ✅ **Case 1: Money Leak Audit (WO-056)** (2026-01-14)
   - Result: PASS. Identified Government Asset sale recording missing in HousingSystem.

---

## ⚙️ Level 3 Automation Roadmap (Review Mode)

| Category | Level | Required review successes for Level 3 |
| :--- | :--- | :--- |
| **Reporter** | **Level 2** | ✅ ⬜ ⬜ |
| **Spec Drafter** | **Level 2** | ✅ ✅ ⬜ |
| **Validator** | **Level 2** | ⬜ ⬜ ⬜ |
| **State Auditor** | **Level 2** | ⬜ ⬜ ⬜ |
| **Git Operator** | **Level 2** | ⬜ ⬜ ⬜ |
| **Context/Git** | **Level 1** | (Need 1 more Calibration success for Context) |
| **Code Auditor** | **Level 1** | ✅ ⬜ ⬜ (Calibration In-progress) |
| **Sync Verifier** | **Level 1** | (Calibration pending) |

