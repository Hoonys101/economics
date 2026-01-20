# Report: Project Cleanliness Audit

## Executive Summary
The project's root and `design` directories contain a significant number of misplaced, redundant, and temporary files that deviate from the established `project_structure.md` and `design/manuals/scr_launcher.md` protocols. A cleanup is required to improve navigation, reduce clutter, and ensure developers use canonical artifacts.

## Detailed Analysis

### 1. Root Directory Cleanup
- **Status**: ⚠️ Partial
- **Evidence**: The root directory contains numerous files that should be located in designated subdirectories.
- **Proposal**:
    - **Move to `scripts/`**:
        - `gemini-go.bat`, `git-go.bat`, `harvest-go.bat`, `jules-go.bat`, `merge-go.bat` (Launcher scripts)
        - `log_selector.py` (Utility script)
        - `run_experiment.py` (Utility script)
        - `verify_banking_v2.py`, `verify_banking_v3.py`, `verify_banking.py`, `verify_maslow.py` (Verification scripts)
    - **Move to a `logs/` directory (or similar git-ignored location)**:
        - `full_log.txt`, `test_log.txt`
    - **Move to `data/` or `results/`**:
        - `ai_model_needs_and_growth.pkl`, `ai_model_needs_and_social_status.pkl`, `ai_model_wealth_and_needs.pkl`
    - **Delete**:
        - `gemini.md.bak` (Backup file)
        - `main` (Empty directory)
        - `app.py` (Redundant; `dashboard/app.py` and `main.py` exist as entry points)

### 2. Redundant Top-Level Directories
- **Status**: ❌ Missing
- **Evidence**: The project contains directories with non-standard (Korean) naming and redundant purposes.
- **Proposal**:
    - **Consolidate `경제 실험 보고서`**: Move contents (`.csv`, `.md`) to `reports/` or `results/` and delete the directory.
    - **Consolidate `설계도_계약들`**: This directory is a direct translation of "Blueprints_Contracts" and contains `specs` and `work_orders` folders, which are redundant with the standard buckets defined in `design/manuals/scr_launcher.md`. Merge any unique contents into the corresponding folders within `design/` and delete this directory.

### 3. `design/` Folder Reorganization
- **Status**: ⚠️ Partial
- **Evidence**: The `design/` directory is used as a catch-all instead of adhering to the "Standard Output Buckets" protocol.
- **Proposal**:
    - **Delete Temporary Artifacts**:
        - `.gemini_step2_wo083c.json` (Temp file)
        - `jules_instruction.txt` (Temp file)
    - **Archive/Consolidate Planning Documents**:
        - `task.md`, `TODO.md` (from root): Merge into `design/project_status.md` and delete.
        - `structure.md`: Appears redundant with `project_structure.md`. Delete.
    - **Move to `design/manuals/`**:
        - `CURRENT_BRIEFING.md`
        - `DEBT_LIQUIDATION_PLAN.md`
        - `ECONOMIC_INSIGHTS.md`
        - `GEMINI_USAGE_MANUAL.md`
        - ...and other general `.md` documentation files currently in the `design/` root.
    - **Consolidate Non-Standard `design/` Subdirectories**:
        - `feedback/`, `roles/`, `test_plans/`: Review and move contents to `design/drafts/` or `design/_archive/`, then delete these directories.
        - `test_reports/`: Move contents to the root `reports/` directory and delete.

## Risk Assessment
- **Configuration Risk**: Stale `.bat` scripts or configuration files in the root can be used by mistake, leading to incorrect behavior.
- **Reduced Discoverability**: Core documents are difficult to locate, forcing developers to guess which file is canonical (e.g., `structure.md` vs. `project_structure.md`).
- **Increased Cognitive Load**: A cluttered workspace slows down development and increases the chance of human error.

## Conclusion
The project structure has eroded, leading to significant clutter. A refactoring effort is recommended to move files to their designated locations as outlined in the project's own documentation (`project_structure.md` and `design/manuals/scr_launcher.md`). This will enforce consistency and improve developer efficiency.
