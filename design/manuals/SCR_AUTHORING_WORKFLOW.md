# 📜 SCR (Structured Command Registry) Authoring Workflow
> **File**: `design/manuals/SCR_AUTHORING_WORKFLOW.md`
> **Purpose**: Guide for authoring `command_registry.json` to control the Ops Toolkit (Gemini/Jules).

---

## 🏗️ Core Philosophy
The `command_registry.json` is the **Single Source of Truth** for all Agent Operations.
- **Antigravity (AI)**: Writes the JSON entries to define the mission.
- **User (Human)**: Executes the mission via `gemini-go` or `jules-go` menus.

## 📝 JSON Schema & Rules

### 1. General Structure
The root object contains unique keys for each mission. The key name becomes the menu title.

```json
{
  "_meta": {
    "session": "Current Session Name",
    "updated": "YYYY-MM-DD"
  },
  "unique_mission_key": { ... },
  "another_mission": { ... }
}
```

### 2. Gemini Missions (Analysis & Design)
Used for dispatching Gemini workers (`audit`, `spec`, `report`, `git-review`).

| Field | Type | Description |
|---|---|---|
| `worker` | string | **Required**. Worker type: `audit`, `spec`, `git-review`, `context`, `verify`. |
| `instruction` | string | **Required**. The prompt for the agent. Use `\n` for formatting. |
| `context` | list[str] | List of file paths to read. Relative to project root. |
| `output` | string | Optional. Path to save the result markdown file. |
| `model` | string | Optional. `pro` or `flash`. Default is configured in script. |

**Example:**
```json
"td105_hunt": {
  "worker": "audit",
  "instruction": "Find the +320 drift source in bank.py...",
  "context": ["simulation/bank.py", "simulation/tick_scheduler.py"],
  "output": "design/audits/drift_report.md"
}
```

### 3. Jules Missions (Coding & Implementation)
Used for dispatching Jules agents for code modification.

#### A. New Session (`create`)
| Field | Type | Description |
|---|---|---|
| `command` | string | Must be `"create"`. |
| `title` | string | Title of the Task/PR. |
| `instruction` | string | The prompt for Jules. |
| `file` | string | **Optional**. Path to a file (e.g., Spec) whose content will be appended to the instruction. |
| `wait` | bool | Optional. `false` (default). |

**Example:**
```json
"fix_drift": {
  "command": "create",
  "title": "Fix_TD105_Drift",
  "instruction": "Implement the fix as per the spec.",
  "file": "design/specs/TD105_DRIFT_FIX_SPEC.md"
}
```

#### B. Reply / Follow-up (`send-message`)
Used to send a pre-defined message to an active session via the interactive menu.

| Field | Type | Description |
|---|---|---|
| `command` | string | Must be `"send-message"`. |
| `instruction` | string | The message content. |
| `file` | string | **Optional**. Path to a file to inject into the message (e.g., Updated Spec). |

**Example:**
```json
"reply_with_spec": {
  "command": "send-message",
  "instruction": "Please review the updated logical flow in the attached spec.",
  "file": "design/specs/UPDATED_SPEC.md"
}
```

---

## 🚦 Workflow for Antigravity

1.  **Define Goal**: What needs to be done? Analysis (Gemini) or Coding (Jules)?
2.  **Prepare Files**:
    - If it's a Jules mission, first ensure the **Spec File** exists (`design/specs/...`).
    - If it's a Gemini mission, identify the **Context Files** (`simulation/...`).
3.  **Update Registry**:
    - Use `write_to_file` to update `command_registry.json`.
    - **Overwrite** the file with the new set of relevant missions. (Keep missions relevant to the *current* session only to avoid clutter).
4.  **Notify User**:
    - Inform the user: *"Missions loaded. Run `gemini-go` and select 'X' to start."*

## ⚠️ Anti-Patterns (Do NOT do this)
- **Do NOT** try to run `gemini-go` or `jules-go` directly via `run_command`.
- **Do NOT** include absolute paths (e.g., `C:\...`) in the JSON. Use relative paths.
- **Do NOT** forget to specify `worker` for Gemini tasks.

