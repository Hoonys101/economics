# 🛠️ Protocol: Tooling & Operations (SCR)

This protocol defines how to use the project's automation tools via the **Structured Command Registry (SCR)**.

---

## 🏗️ 1. The Core Principle: Data-Driven Control
We do not modify `.bat` files or run complex CLI commands directly. Instead:
1.  **Register**: Define the mission in `design/command_registry.json`.
2.  **Fire**: Run the corresponding `.bat` file (e.g., `gemini-go.bat`).

---

## 🤖 2. Gemini (Analysis & Design)
Gemini handles planning, auditing, and specification.

### Worker Types:
- **`audit`**: Structural analysis (God classes, circular imports, leaks).
- **`spec`**: Technical specification drafting (Interface + Pseudocode).
- **`git-review`**: PR analysis (Security & Integrity).
- **`verify`**: Rule compliance checking.

### JSON Configuration:
```json
"gemini": {
  "worker": "audit | spec | verify",
  "instruction": "Detailed prompt for the agent.",
  "context": ["path/to/file1.py", "path/to/file2.py"],
  "output": "design/specs/RESULT.md",
  "audit": "Optional. Path to audit report (context for spec mode).",
  "model": "pro (default) | flash"
}
```

---

## 👩‍💻 3. Jules (Implementation)
Jules is the primary agent for code modification.

### Commands:
- **`create`**: Start a new implementation task.
- **`send-message`**: Provide feedback or answer questions in an active session.

### JSON Configuration:
```json
"jules": {
  "command": "create | send-message",
  "title": "Task title (e.g., WO-116_Inheritance_Fix)",
  "instruction": "What to do. TASKS: 1..., REFERENCE: spec.md",
  "file": "Optional. Path to a file to inject into the prompt.",
  "session_id": "Required for send-message.",
  "wait": true
}
```

---

## 🔍 4. Git & Review Operations (git-go)
Used for branch management and diff analysis.

### JSON Configuration:
```json
"git_review": {
  "branch": "feature/branch-name",
  "instruction": "Focus areas (e.g., 'Check zero-sum logic in bank.py')"
}
```

---

## ⌨️ 5. Implementation Shortcuts (cmd_ops.py)
Use `python scripts/cmd_ops.py` to populate the registry via CLI.

- **Set Gemini Task**:
  `python scripts/cmd_ops.py set-gemini <name> --worker audit -i "Find leaks" -c simulation/bank.py`
- **Set Jules Task**:
  `python scripts/cmd_ops.py set-jules <name> --command create -t "Fix bug" -i "Use spec" -f design/specs/spec.md`

---

## 🚨 Guidelines & Anti-Patterns
1.  **Context is King**: Always provide relevant DTOs/Interfaces for `spec` tasks.
2.  **Template Inheritance**: Copy `design/templates/command_registry_template.json` if the registry gets corrupted.
3.  **No Absolute Paths**: Never use `C:\...` in JSON. Use relative paths.
4.  **Windows Escaping**: In `cmd_ops.py`, use double quotes (`"`) for strings containing spaces.
