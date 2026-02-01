# 🛠️ Troubleshooting: Git & Operations

This document tracks common Git-related friction points and provides standardized solutions. Refer to this before asking for help or escalating to the Architect.

---

## 🛑 1. Local Changes Blocking Checkout
**Error**: `error: Your local changes to the following files would be overwritten by checkout: ... Please commit your changes or stash them.`

### **Why it happens**
You (or an agent) modified files (e.g., `command_registry.json`, `QUICKSTART.md`) but didn't commit them. `merge-go.bat` or `git checkout main` cannot proceed because it would lose these changes.

### **Solution**
1.  **Commit them** (Recommended for documentation updates):
    ```powershell
    git add .
    git commit -m "docs: sync local changes before merge"
    ```
2.  **Stash them** (If you want to discard/save for later):
    ```powershell
    git stash
    # After merge/checkout
    git stash pop
    ```

---

## 🖇️ 2. Remote Branch Merge & Lock Errors
**Error**: `! [remote rejected] ... (cannot lock ref ...: unable to resolve reference)` or `ls-remote` failures.

### **Why it happens**
- The branch was already deleted on the remote but your local Git still thinks it exists.
- Simultaneous operations on the remote.

### **Solution**
1.  **Prune and Sync**:
    ```powershell
    git fetch --prune
    ```
2.  **Verify Remote State**:
    ```powershell
    git ls-remote --heads origin
    ```
    If the branch is NOT in the list, it's already gone. You can safely stop the merge sequence.

---

## 🔄 3. `merge-go.bat` Failures
**Error**: Merge sequence interrupted at `git checkout main` or `git merge`.

### **Checklist**
1.  **Are you on the correct branch?** Always start `merge-go.bat` from the feature branch you want to merge.
2.  **Unresolved Conflicts**: If a merge fails, look for `UU` status in `git status -s`. Manually resolve conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`), then `git add` and `git commit`.
3.  **Registry Desync**: If `command_registry.json` is the cause, decide whether to keep your local mission status or use the one from `main`.

---

## 🧹 4. Cleaning up Orphaned Branches
If you have too many old local branches:

```powershell
# Delete merged branches
git branch --merged | Select-String -NotMatch "main", "feature/integrity-refactor" | ForEach-Object { git branch -d $_.ToString().Trim() }
```

---

## 🚀 Pro-Tip: The "Sacred Sync"
Before starting any major operation (`jules-go`, `gemini-go`, `merge-go`), run:
`git fetch --prune`
Это ensures your local view of the universe matches the remote.
