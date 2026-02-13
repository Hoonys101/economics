# Audit Report: Targeted Report Harvester Refactoring

## Executive Summary
Current `report_harvester.py` logic is functional but lacks specific targeting for audit reports and lacks batch processing constraints. The proposed refactor will implement a 3-cycle loop processing the top 3 latest branches per cycle, specifically targeting `AUDIT_REPORT_*.md` files as defined in the `AUDIT_SPEC_*.md` manuals.

## Detailed Analysis

### 1. Remote Branch Selection
- **Status**: ⚠️ Partial
- **Evidence**: `report_harvester.py:L31-43` fetches all remote branches sorted by date but processes all of them.
- **Notes**: Needs slicing `[:3]` to satisfy the requirement of selecting only the top 3.

### 2. Targeted File Collection
- **Status**: ⚠️ Partial
- **Evidence**: `report_harvester.py:L45-63` uses `diff --diff-filter=A` to find any new `.md` files in `REPORT_DIRS`.
- **Notes**: Requirement specifies targeting `AUDIT_REPORT_*.md` within `reports/audit/`. Current logic is too broad.

### 3. Loop Structure & Batching
- **Status**: ❌ Missing
- **Evidence**: `report_harvester.py:L84-118` runs once and finishes.
- **Notes**: Must implement a `for _ in range(3):` loop to enable repetitive harvesting cycles.

### 4. Log Format Improvement
- **Status**: ⚠️ Partial
- **Evidence**: `report_harvester.py:L120-137` uses a simple bulleted list.
- **Notes**: Needs metadata enrichment (Branch ID, Timestamp, Specific Audit Type).

---

## Refactoring Plan (Implementation Specification)

### Step 1: Define Target Constants
Add explicit mapping based on `AUDIT_SPEC_*.md`:
```python
TARGET_AUDIT_FILES = {
    "ECONOMIC": "reports/audit/AUDIT_REPORT_ECONOMIC.md",
    "PARITY": "reports/audit/AUDIT_REPORT_PARITY.md",
    "STRUCTURAL": "reports/audit/AUDIT_REPORT_STRUCTURAL.md"
}
LOCAL_AUDIT_DIR = "reports/audit/"
```

### Step 2: Update `get_remote_branches`
Modify to return exactly 3 branches:
```python
def get_top_remote_branches(limit: int = 3) -> List[str]:
    # ... existing git fetch and sort logic ...
    return all_remote_branches[:limit]
```

### Step 3: Targeted File Discovery
Replace `get_new_files_in_branch` with a presence-check for defined audit reports:
```python
def get_audit_files_in_branch(branch: str) -> List[str]:
    found = []
    for audit_type, file_path in TARGET_AUDIT_FILES.items():
        # Check if file exists in the specific remote branch
        check = run_command(["git", "ls-tree", "-r", branch, "--name-only"])
        if file_path in check.split("\n"):
            found.append(file_path)
    return found
```

### Step 4: Implement 3-Cycle Loop
Wrap the `harvest` logic:
```python
def harvest_cycle():
    for i in range(3):
        print(f"[Harvester] Starting Cycle {i+1}/3")
        branches = get_top_remote_branches(limit=3)
        if not branches:
            break
        # ... processing logic ...
```

### Step 5: Metadata Log Format
Improve `update_log` to use a structured table or detailed blocks:
```python
def update_log(new_entries: List[dict]):
    # Format: | Timestamp | Branch | Audit Type | Local Path |
```

## Risk Assessment
- **Branch Deletion Race Condition**: If the loop runs too fast or git fetch isn't updated, it might try to delete already deleted branches.
- **File Overwrites**: Multiple branches might contain the same audit report filename; `safe_name` logic in `L102` must be robust.

## Conclusion
The script requires a shift from "Generic MD Harvester" to "Specific Audit Collector". Implementing the 3x3 batching logic (3 cycles of 3 branches) ensures controlled automation and clean remote state management.

---

**Insight Report Created**: `communications/insights/audit-harvester-logic.md` (Drafting required upon implementation).