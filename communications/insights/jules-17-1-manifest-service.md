# Architectural Insight: Spec 17.1 (Manifest Migration)

## 1. Technical Debt Retired
-   **TD-SYS-BATCH-FRAGILITY (Data as Code)**: Replaced the fragile `command_manifest.py` (which was missing from the repo but referenced in specs) with a robust `mission_db.json` managed by `MissionRegistryService`.
-   **TD-SYS-REGEX-PARSING**: Eliminated the need for regex-based editing of Python files for mission management.
-   **TD-ENV-MISSING-FILES**: Identified and mitigated the absence of `launcher.py` and `_internal` directory by creating a new `MissionRegistryService` and `scripts/mission_launcher.py`.

## 2. Architectural Decisions
-   **Protocol Injection Pattern**: Implemented `MissionRegistryService.get_mission_prompt` to dynamically inject `META`, `GUARDRAILS`, and `OUTPUT_DISCIPLINE` into mission prompts. This ensures that even old pending missions use the latest safety protocols.
-   **Service-Based Locking**: Implemented `MissionLock` within the service to ensure transactional integrity during mission registration and deletion.
-   **Launcher Replacement**: Since the original `launcher.py` was not present in the repository, a new `scripts/mission_launcher.py` was created to interface with the `MissionRegistryService`. This script provides `list`, `create`, `run`, `delete`, and `migrate` commands.
-   **DTO Purity**: Defined strict `MissionDTO` and `MissionType` in `_internal.registry.api` to ensure data consistency across boundaries.

## 3. Risk Analysis
-   **Migration One-Way Valve**: The migration from `command_manifest.py` is supported but relies on the file being present. Since the file was missing in this environment, the migration logic was verified via unit tests with a dummy file.
-   **Environment Consistency**: The `_internal` directory was missing and had to be created and un-ignored in `.gitignore`. This might cause conflicts if the user has a local `_internal` directory with different content. The new service is isolated in `_internal/registry`.
-   **Missing Protocol Fix**: During testing, a missing `IHouseholdFactory` in `modules/simulation/api.py` was blocking tests (via `conftest.py`). This was fixed by adding the missing protocol definition, restoring environment health.

## 4. Test Evidence
The following tests confirm the functionality of `MissionRegistryService` and the migration logic:

```bash
$ python -m pytest tests/unit/registry/test_service.py
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /app
configfile: pytest.ini
plugins: asyncio-0.25.3, anyio-4.12.1, mock-3.15.1
collected 7 items

tests/unit/registry/test_service.py::test_load_missions_empty PASSED     [ 14%]
tests/unit/registry/test_service.py::test_register_and_get_mission PASSED [ 28%]
tests/unit/registry/test_service.py::test_delete_mission PASSED          [ 42%]
tests/unit/registry/test_service.py::test_get_mission_prompt PASSED      [ 57%]
tests/unit/registry/test_service.py::test_migration PASSED               [ 71%]
tests/unit/registry/test_service.py::test_lock_timeout PASSED            [ 85%]
tests/unit/registry/test_service.py::test_lock_success PASSED            [100%]

============================== 7 passed in 0.50s ===============================
```

## 5. Usage Guide
Since `launcher.py` was replaced, use `scripts/mission_launcher.py`:

```bash
# List missions
python scripts/mission_launcher.py list

# Create a mission
python scripts/mission_launcher.py create my-key --type jules --title "My Mission" --instruction "Do X"

# Run a mission (get prompt)
python scripts/mission_launcher.py run my-key

# Delete a mission
python scripts/mission_launcher.py delete my-key

# Migrate legacy
python scripts/mission_launcher.py migrate path/to/command_manifest.py
```
