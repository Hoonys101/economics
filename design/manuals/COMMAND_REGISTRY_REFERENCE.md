# 📖 Reference: Structured Command Registry (SCR)

The **Structured Command Registry** (`design/command_registry.json`) is the central database that defines missions for the project's AI agents. While `cmd_ops.py` is the preferred interface for basic operations, this document provides a deep dive into the underlying data structure and advanced manual configuration.

---

## 🏗️ 1. JSON Data Structure

The registry is a JSON object where each key represents a **Mission Key**.

### 🤖 Gemini Mission Schema
Used for analysis, auditing, and specification writing via `gemini-go.bat`.

```json
"mission-key": {
  "worker": "audit | spec | git-review | context | verify",
  "instruction": "The primary prompt for Gemini.",
  "context": ["path/to/file1.py", "path/to/file2.py"],
  "output": "path/to/output.md",
  "audit": "Optional: Path to a previous audit report for context.",
  "model": "Optional: 'pro' (default) or 'flash'"
}
```

### 👩‍💻 Jules Mission Schema
Used for implementation and debugging via `jules-go.bat`.

```json
"mission-key": {
  "command": "create | send-message",
  "title": "Short descriptive title (Required for 'create')",
  "instruction": "Detailed tasks and implementation rules.",
  "file": "Optional: Path to a specification or work order file to inject.",
  "session_id": "Required for 'send-message' to identify the active session.",
  "wait": true
}
```

---

## 🛠️ 2. Advanced Manual Patching

In rare cases where `cmd_ops.py` is insufficient, you may edit `command_registry.json` directly. Follow these strict rules:

1.  **Relative Paths Only**: Never use absolute paths (e.g., `C:\...`). All paths must be relative to the project root.
2.  **No Escaping Issues**: Ensure all backslashes in paths are escaped (e.g., `simulation/systems/bank.py`) or use forward slashes.
3.  **Unique Keys**: Ensure every mission has a unique key.
4.  **Metadata**: Preserve the `_meta` key for session tracking.

---

## 🆘 3. Troubleshooting & Recovery

### Corruption Recovery
If the JSON becomes malformed, check `design/templates/command_registry_template.json` (if available) or revert via Git.

### Worker Errors
- **"Key not found"**: Ensure the exact key passed to the `.bat` file exists in the JSON.
- **"Instruction missing"**: Ensure the `instruction` field is present and not empty.

---

## 🔗 Related Documents
- **[PROTOCOL_TOOLING.md](PROTOCOL_TOOLING.md)**: Standard operating procedures using `cmd_ops.py`.
- **[QUICKSTART.md](QUICKSTART.md)**: Entry point for general workflow.
