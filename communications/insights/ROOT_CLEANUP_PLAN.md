# Root & Folder Architecture Audit Report (WO-AUDIT-ROOT-CLEANUP)

## Executive Summary
The current project structure exhibits significant "structural drift" from the **Antigravity Era Standard** defined in `design/1_governance/project_structure.md`. Approximately 70% of top-level directories and 90% of root-level files are non-compliant, leading to context dilution for AI agents and increased architectural maintenance overhead.

## Detailed Analysis

### 1. Folder Structure Compliance Audit
| Directory | Status | Standard Mapping / Action |
| :--- | :--- | :--- |
| `_internal/` | ✅ Compliant | System core, registry, scripts. |
| `design/` | ✅ Compliant | Governance and artifacts. |
| `modules/` | ✅ Compliant | Business domain logic. |
| `simulation/` | ✅ Compliant | Simulation engine. |
| `communications/` | ✅ Compliant | Logs and insights. |
| `tests/` | ✅ Compliant | Quality verification. |
| `analysis/`, `analysis_report/` | ❌ Non-Std | Move to `design/3_work_artifacts/reports/`. |
| `artifacts/`, `reports/`, `results/` | ❌ Non-Std | Consolidate into `design/3_work_artifacts/reports/`. |
| `audits/` | ❌ Non-Std | Move to `design/3_work_artifacts/reports/` (reports) or `_internal/scripts/` (tools). |
| `benchmarks/` | ❌ Non-Std | Relocate to `tests/benchmarks/`. |
| `config/` | ⚠️ Partial | Move into `modules/common/config/` or `_internal/registry/`. |
| `dashboard/`, `watchtower/`, `static/` | ❌ Non-Std | Consolidate into a single `interface/` or `modules/visualization/`. |
| `data/` | ❌ Non-Std | Move to `simulation/data/` or `modules/common/data/`. |
| `docs/` | ❌ Non-Std | Merge into `design/1_governance/` or `design/3_work_artifacts/context/`. |
| `experiments/`, `scenarios/` | ❌ Non-Std | Relocate to `simulation/scenarios/`. |
| `gemini-output/` | ❌ Non-Std | Relocate to `design/3_work_artifacts/reports/inbound/`. |
| `logs/` | ❌ Non-Std | Consolidate into `communications/jules_logs/` or `_archive/`. |
| `scripts/` | ❌ Non-Std | Merge into `_internal/scripts/`. |
| `tools/`, `utils/` | ❌ Non-Std | Move to `modules/common/utils/` or `_internal/scripts/`. |

### 2. Root Script & Utility Audit (Orphan Files)
The root directory is currently polluted with 100+ transient files. 
- **Diagnostic Logs (60+ files)**: Files like `trace_output_*.txt`, `verification_output_*.txt`, `pytest_*.txt`, and `batch_results.txt` should be moved to `_archive/snapshots/` or deleted.
- **Debug/Fix Scripts (25+ files)**: Scripts such as `debug_*.py`, `fix_*.py`, `verify_*.py`, and `check_*.py` represent "Duct-Tape Debugging" artifacts. 
    - **Action**: Move valid tools to `_internal/scripts/` and archive/delete one-time fixes.
- **Temporary State Files**: `test.db`, `simulation.lock`, `instances.txt` should be ignored via `.gitignore` or moved to a dedicated `temp/` or `data/` directory.
- **Project Documentation**: `HANDOVER.md` and `PROJECT_STATUS.md` are standard but `project_structure_report.txt` and `tree_audit.txt` are redundant artifacts.

## Risk Assessment
- **Context Dilution**: AI workers (Gemini/Jules) may ingest redundant or conflicting diagnostic logs, leading to hallucinations or "GIGO" outcomes.
- **Tool Confusion**: Multiple `scripts/`, `tools/`, and `_internal/scripts/` directories create ambiguity regarding the "Single Source of Truth" for system utilities.
- **Vibe Check**: High risk. The proliferation of `fix_*.py` and `temp_*.py` files in the root indicates a pattern of unprincipled modification rather than adherence to the **Artifact-Driven Development** protocol.

## Conclusion
The project requires a **Phase 0: Deep Cleanup** mission. 
1. **Consolidate Artifacts**: Merge all `analysis`, `reports`, and `results` folders into `design/3_work_artifacts/`.
2. **Evacuate Root**: Move all diagnostic `.txt` and temporary `.py` scripts to `_archive/` or `_internal/scripts/`.
3. **Enforce Standards**: Strictly adhere to the `_internal/` and `design/` hierarchies for all future system and documentation tasks.