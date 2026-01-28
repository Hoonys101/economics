# 🛠️ Protocol: Tooling & Operations (SCR)

This protocol defines the standard workflow for interacting with the **Structured Command Registry (SCR)** using the command-line interface.

---

## 🏗️ 1. The Core Principle: Interface over Implementation
To ensure registry integrity and ease of use, we interact with the system via the `scripts/cmd_ops.py` utility.

- **Standard User Flow**: Use `cmd_ops.py` for all mission assignments.
- **Architect Privilege**: Direct JSON editing in `command_registry.json` is reserved for the AI Orchestrator (Antigravity) or advanced manual recovery.

---

## 🤖 2. Managing Gemini Missions (Analysis/Spec)
Gemini handles planning, auditing, and log analysis.

### Standard Command
```powershell
python scripts/cmd_ops.py set-gemini <mission_key> --worker [audit|spec|git-review|verify] -i "<instruction>" -c <context_files...>
```

### Common Examples
| Worker | Purpose | Typical Instruction |
|---|---|---|
| `audit` | Find leaks/bugs | "Analyze logs/forensics.log and identify asset leaks." |
| `spec` | Draft logic | "Create a technical spec for the SettlementSystem based on audit_report.md" |
| `git-review` | Audit PRs | "Review branch feature/fix-leak for security and purity." |

---

## 👩‍💻 3. Managing Jules Missions (Implementation)
Jules is the primary agent for code modification.

### Standard Command
```powershell
python scripts/cmd_ops.py set-jules <mission_key> --command [create|send-message] -t "<task_title>" -i "<instruction>" -f <spec_file>
```

### Key Arguments
- `--command create`: Starts a brand new coding session.
- `--command send-message`: Replies to an existing session (Requires `session_id` in JSON, usually handled by Antigravity).
- `-f / --file`: Injects a work order or spec file into Jules's initial prompt.

---

## 🧹 4. Registry Maintenance
To keep the registry clean, delete finished or irrelevant missions:

```powershell
python scripts/cmd_ops.py del <mission_key>
```

---

## 🚨 Guidelines & Anti-Patterns
1.  **No Absolute Paths**: `cmd_ops.py` handles paths relative to the root. Do not use `C:\...`.
2.  **Instruction Quality**: Be specific. Link to work orders (e.g., `-f design/work_orders/WO-124.md`).
3.  **Verification**: After arming the tool, always run the corresponding `.bat` file (e.g., `.\gemini-go.bat <key>`).

---

## 🔗 Advanced Reference
For detailed JSON schema and manual patching rules, see:
**[COMMAND_REGISTRY_REFERENCE.md](COMMAND_REGISTRY_REFERENCE.md)**
