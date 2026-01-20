# Mission: Infrastructure & Script Maintenance (TD-050, TD-063, TD-051)

## Context
As the project grows, our utility scripts and documentation need stabilization. You are assigned to clean up import logic, exclude noise from health reports, and finalize documentation IDs.

## Task Details

### 1. Stable Import Logic (TD-063)
- **Problem**: Many scripts in `scripts/` use `sys.path.append(os.path.join(os.path.dirname(__file__), '..'))` which is brittle and can fail depending on execution context.
- **Action**: Refactor all scripts in `scripts/` to use `pathlib` for project root detection.
- **Goal**: Ensure consistent behavior when run from any directory.

### 2. Cleanup Health Reports (TD-050)
- **Problem**: `scripts/scan_codebase.py` (or similar audit scripts) scans `scripts/observer/`, leading to false positive complexity alerts in third-party or observer-only code.
- **Action**: Update the scanning logic to exclude the `scripts/observer/` and `design/` (artifacts) directories from the complexity/SoC analysis.

### 3. Documentation Sanitization (TD-051)
- **Problem**: Some manuals or specs still contain `WO-XXX` placeholders instead of concrete task IDs.
- **Action**: Grep for any remaining `WO-XXX` in the `design/` folder and replace them with the actual Work Order IDs (e.g., `WO-083C`) based on the contents of the file or `TECH_DEBT_LEDGER.md`.

## Verification Requirements
- All refactored scripts must still run correctly (e.g., `python scripts/launcher.py --help`).
- Run the health scan script and verify `scripts/observer` is no longer in the report.
- `grep -r "WO-XXX" design/` should return zero results.

## Success Criteria
- ✅ Import logic homogenized using `pathlib`.
- ✅ Health reports are noise-free.
- ✅ Documentation is free of placeholders.
