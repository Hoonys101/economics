# 🛠️ Protocol: Tooling & Operations (SCR)

This protocol defines the standard workflow for interacting with the **Structured Command Registry (SCR)** using the command-line interface.

---

## 🏗️ 1. The Core Principle: Interface over Implementation
The **Structured Command Registry (SCR)** is the central hub for mission delegation. We favor direct interaction with the source for maximum precision.

- **Architect's Workflow (Preferred)**: Edit [`command_registry.py`](file:///_internal/registry/command_registry.py) directly. This allows for rich comments, multi-line strings, and full architectural context.
- **Legacy/Utility Flow**: Use `_internal/scripts/cmd_ops.py` for simple, one-shot mission assignments.

---

## 🤖 2. Managing Gemini Missions (Analysis/Spec)
Gemini handles planning, auditing, and log analysis.

### Standard Workflow (Direct Edit)
Add an entry to the `GEMINI_MISSIONS` dict in `gemini_manifest.py`.

### Legacy Command
```powershell
python _internal/scripts/cmd_ops.py set-gemini <mission_key> --worker [spec|reporter|audit|git|git-review|verify|context|crystallizer] -i "<instruction>" -c <context_files...>
```

### Common Examples
| Worker | Purpose | Typical Instruction |
|---|---|---|
| `reporter` | Find leaks/bugs | "Analyze logs/forensics.log and identify asset leaks." |
| `spec` | Draft logic | "Create a technical spec for the SettlementSystem based on audit_report.md" |
| `audit` | Consistency audit | "Check for architectural rule violations in simulation/engine.py" |
| `git-review` | Audit PRs | "Review branch feature/fix-leak for security and purity." |
| `crystallizer` | Insight Extract | "Distill key takeaways from the recent integration test failures into a Spec." |

---

## 👩‍💻 3. Managing Jules Missions (Implementation)
Jules is the primary agent for code modification.

### Standard Workflow (Direct Edit)
Define a mission with `command: "create"` or `command: "send-message"`. For complex tasks, use triple-quotes (`"""`) for the `instruction` field.

### Legacy Command
```powershell
python _internal/scripts/cmd_ops.py set-jules <mission_key> --command [create|send-message] -t "<task_title>" -i "<instruction>" -f <spec_file>
```

### Key Arguments
- `--command create`: Starts a brand new coding session.
- `--command send-message`: Replies to an existing session (Requires `session_id` in JSON, usually handled by Antigravity).
- `-f / --file`: Injects a work order or spec file into Jules's initial prompt.

---

## 🧹 4. Registry Maintenance
To keep the registry clean, delete finished or irrelevant missions:

```powershell
python _internal/scripts/cmd_ops.py del <mission_key>
```
*Alternatively, simply delete the key-value pair from the Python dictionary.*

---

## 🚨 Guidelines & Anti-Patterns
2.  **No Absolute Paths**: All paths must be relative to the root. Do not use `C:\...`.
2.  **Instruction Quality**: Be specific. Reference specs (e.g., `design/3_work_artifacts/specs/MISSION_spec-XYZ_SPEC.md`).
3.  **Verification**: After saving the manifest, run the corresponding `.bat` file (e.g., `.\gemini-go.bat <key>`).
4.  **Choice Adherence**: Always consult the `# --- CHOICE REFERENCE ---` in the registry file before selecting a worker or command.

---

## 🔗 Advanced Reference
For detailed JSON schema and manual patching rules, see:
**[COMMAND_REGISTRY_REFERENCE.md](COMMAND_REGISTRY_REFERENCE.md)**
