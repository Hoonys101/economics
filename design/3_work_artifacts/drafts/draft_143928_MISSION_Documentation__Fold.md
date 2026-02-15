# Documentation Governance Standard (UPS-4.2)

> **Document ID**: `PROTOCOL-DOC-001`
> **Version**: 1.0.0
> **Status**: Active
> **Last Updated**: 2026-02-15

---

## 1. Governance Hierarchy & Directory Structure

This protocol establishes the **Single Source of Truth (SSoT)** for all project documentation. Adherence to this structure is mandatory for all agents (Human, Gemini, Jules).

### 1.1. Directory Structure Map

| Directory | Role | Write Access | Lifecycle |
| :--- | :--- | :--- | :--- |
| **`design/1_governance/`** | **The Constitution**. Normative standards, architecture specs, and core protocols. | **Architect Only** | Permanent, Versioned |
| **`design/2_operations/`** | **The Playbook**. Procedures, templates, manual guides, and operational ledgers. | **Architect/Gemini** | Active, Evolving |
| **`design/3_work_artifacts/`** | **The Workbench**. Active Specs, Audits, Plans, and Work Orders. | **All Agents** | Active -> Archive |
| **`communications/`** | **The Signal Pipeline**. Inbound reports, active logs, requests. | **All Agents** | Transient (Session-bound) |
| **`_archive/`** | **The Vault**. Processed artifacts, closed phases, crystallized insights. | **System** | Read-Only (Historical) |

### 1.2. Anti-Patterns (Strictly Prohibited)
- ❌ **Root Clutter**: Creating `.md` or `.csv` files in the project root (e.g., `/reports/`, `/logs/`). All artifacts must reside in `design/` or `communications/`.
- ❌ **Shadow Governance**: Creating documentation in `_internal/manuals/`. This directory is deprecated for general docs.
- ❌ **Zombie Inbound**: Leaving files in `inbound/` folders for more than 1 session. They must be processed or archived.

---

## 2. Artifact Lifecycle Protocols

### 2.1. The Ingestion Pipeline (Inbound -> Ledger -> Archive)
All generated reports and insights follow this flow to prevent "write-only" graveyards.

1.  **Creation**: Agent generates report in `communications/insights/` (e.g., `jules-fix-bug.md`).
2.  **Processing**: Architect/Gemini reads the report during **Crystallization**.
    - Critical findings -> Merged into `TECH_DEBT_LEDGER.md` or `ARCHITECTURAL_INSIGHTS.md`.
    - Status updates -> Merged into `PROJECT_STATUS.md`.
3.  **Archival**:
    - **Valuable**: Moved to `design/_archive/insights/YYYY-MM/`.
    - **Transient**: Deleted via `cleanup-go.bat`.

### 2.2. Work Artifacts (Specs & Audits)
- **Active Specs**: Reside in `design/3_work_artifacts/specs/`.
- **Active Audits**: Reside in `design/3_work_artifacts/audits/`.
- **Completed**: Once implemented, the Spec is **NOT** deleted but moved to `design/_archive/specs/` to preserve intent history.

---

## 3. Mandatory Document Templates

All agents must use these templates. Hallucinated formats are rejected.

### 3.1. Insight Report Template (`communications/insights/`)
Used for reporting findings, bug fixes, or architectural risks.

```markdown
# Insight: [Title]
- **Date**: YYYY-MM-DD
- **Author**: [Agent Name]
- **Related Mission**: [Mission Key/ID]

## 1. Summary
[Brief 1-2 sentence overview]

## 2. Key Findings
- [ ] **Critical**: [Blocking issue]
- [ ] **Major**: [Architectural deviation]
- [ ] **Minor**: [Optimization opportunity]

## 3. Technical Debt Added
| ID | Description | Location |
| :--- | :--- | :--- |
| TD-XXX | [Description] | [File/Module] |

## 4. Verification (Mandatory)
```bash
# Paste verified test output here
pytest ...
```
```

### 3.2. Specification Template (`design/3_work_artifacts/specs/`)
Used for defining new features or refactoring tasks.

```markdown
# Spec: [Title]
- **Target Module**: `modules/...`
- **Dependencies**: [List dependencies]

## 1. Objective
[Clear goal of this specification]

## 2. Architecture & Logic
### 2.1. Data Flow
[Input] -> [Process] -> [Output]

### 2.2. Interface Changes (Pseudo-code)
```python
class MyComponent:
    def execute(self, ctx: Context) -> Result:
        ...
```

## 3. Implementation Plan
- [ ] **Step 1**: [Description]
- [ ] **Step 2**: [Description]

## 4. Verification Plan
- **New Tests**: [List test cases]
- **Regression Check**: [List affected components]
```

---

## 4. Inbound Directory Remediation (Immediate Action)

The directory `design/3_work_artifacts/reports/inbound/` is currently fragmented.

### 4.1. Remediation Policy
1.  **Mass Archive**: All files older than 48 hours in `inbound/` must be moved to `design/_archive/reports/inbound_legacy/`.
2.  **Ledger Reconciliation**: A dedicated "Librarian Mission" will be spawned to scan legacy inbound reports and extract missing Technical Debt items into `TECH_DEBT_LEDGER.md`.
3.  **Lockdown**: Agents are prohibited from writing to `design/3_work_artifacts/reports/inbound/`. Use `communications/insights/` for all session-based reporting.

---

## 5. Verification & Compliance

### 5.1. File Naming Convention
- **Specs**: `spec_[topic].md` (e.g., `spec_housing_market.md`)
- **Audits**: `audit_[topic].md` (e.g., `audit_finance_integrity.md`)
- **Work Orders**: `wo-[id]_[description].md` (e.g., `wo-101_fix_leak.md`)
- **Insights**: `[topic]_[date].md` (e.g., `housing_fix_20260215.md`)

### 5.2. Mandatory Reporting Check
- **Compliance**: This document was generated as part of `spec-doc-standardization`.
- **Insight Report**: Architectural insights found during this analysis are recorded in `communications/insights/spec-doc-standardization.md`.

---

> **Authorization**: Antigravity (Architect)
> **Enforcement**: Immediate