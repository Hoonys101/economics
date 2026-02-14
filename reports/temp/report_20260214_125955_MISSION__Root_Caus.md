# Root Cause Analysis: Recurring manual.md Merge Conflicts

## Executive Summary
The "Ghost Key" phenomenon—where missions default to the `manual` key despite being defined with unique identifiers—is caused by a failure in the **Interactive Launcher (`run_jules_interactive.py`)** to pass the identified mission key to the bridge methods. While the non-interactive CLI correctly passes the key, the interactive UI selects the correct mission but discards the key during the final API call, triggering the `mission_key="manual"` default in `jules_bridge.py`.

## Detailed Analysis

### 1. Mission Key Flow Trace
- **Status**: ⚠️ Partial (Broken in Interactive Path)
- **Trace**:
    - `command_manifest.py`: Mission keys (e.g., `analyze-manual-key-leak`) are defined as dictionary keys.
    - `launcher.py`: Correctly extracts the key from the registry and passes it to `jules_bridge.py` via the `--mission-key` flag in non-interactive mode.
    - `jules_bridge.py`: Defines `mission_key: str = "manual"` as a default parameter for `create_session` and `send_message`.
    - `run_jules_interactive.py`: Correctly loads the registry and identifies the mission key, but **omits** the argument when invoking the bridge.

### 2. Interaction Point Failure
- **Status**: ❌ Missing Parameter Passing
- **Evidence**:
    - `run_jules_interactive.py:L104` (Custom Mission): `bridge.create_session` is called without `mission_key`, defaulting to `"manual"`.
    - `run_jules_interactive.py:L142` (Registered Mission): The local variable `key` holds the correct mission name, but the call to `bridge.create_session` only passes `prompt`, `title`, and `automation_mode`.
    - `run_jules_interactive.py:L218` (Reply Mission): `bridge.send_message(sid, message)` is called without the `mission_key=key` argument.

### 3. Impact on Reporting
- **Status**: ❌ Protocol Violation
- **Evidence**: `jules_bridge.py:L114` and `L183` call `construct_mission_prompt(mission_key, ...)` using the defaulted `"manual"` value.
- **Consequence**: `mission_protocol.py:L56` calculates `insight_path` as `communications/insights/manual.md`. Because every session reports to the same file, Git merge conflicts are guaranteed during parallel or sequential tasks.

## Risk Assessment
- **Technical Debt**: The use of positional-dependent default arguments in `JulesBridge` makes it easy to forget the `mission_key` parameter when adding new UI features.
- **Operational Risk**: High. Continuous merge conflicts in `manual.md` disrupt the "Clean Room Era" protocol and prevent automated PR merging.

## Conclusion
The issue is localized to `_internal/scripts/run_jules_interactive.py`. The "Ghost Key" exists in the interactive menu's logic but is dropped before reaching the API. 

### Proposed Fix
Modify `run_jules_interactive.py` to explicitly pass the `mission_key` in all bridge calls:
1. **Registered Create**: `bridge.create_session(..., mission_key=key)`
2. **Registered Reply**: `bridge.send_message(..., mission_key=key)`
3. **Custom Mission**: Optionally generate a timestamp-based key or force a user-defined key instead of defaulting to `manual`.