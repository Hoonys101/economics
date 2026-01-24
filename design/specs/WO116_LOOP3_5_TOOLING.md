# MISSION: WO-116 Loop 3.5 (Refine Verification Tool)

## 1. SITUATION
- We are trying to verify the -680k fix, but `diagnose_money_leak.py` produces excessive logs (60k+ lines), making analysis impossible.
- The `gemini-cli` fails to process such large files.

## 2. GOAL: Refine `diagnose_money_leak.py`
Modify the diagnosis script to be "Silence by Default, Loud on Error".

### Requirements:
1. **Suppress Noise**: Configure the logger to block `DEBUG` and `INFO` logs from the simulation engine. Only show `DIAGNOSE` level logs.
   - Hint: Use `logging.getLogger().setLevel(logging.WARNING)` or similar to suppress sub-module logs.
2. **Structured Output**: Ensure the script prints a simple summary for each tick:
   `TICK: 100 | LEAK: 0.0000 | TOTAL_M2: 1,500,000`
3. **Self-Verification**:
   - The script should calculate the **Max Absolute Leak** over the run.
   - At the end of the run, print a final verdict.
   - If Max Leak > 1.0, print `[FAIL] Significant Leak Detected`.
   - If Max Leak <= 1.0, print `[SUCCESS] No Significant Leak`.

## 3. DELIVERABLE
- Updated `scripts/diagnose_money_leak.py`.
- Run it once to prove it produces clean output (save output to `design/REPORTS/refined_diagnosis.txt`).
