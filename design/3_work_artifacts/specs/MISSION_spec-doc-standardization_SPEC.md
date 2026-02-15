# Documentation Governance Standard (UPS-4.2)

> **Authority**: This document defines the strict protocol for creating, storing, and archiving project documentation. All Agents (Jules, Gemini) and Human Operators must adhere to this standard to prevent information fragmentation.

---

## 1. The Documentation Architecture (Directory Map)

We enforce a **Single Source of Truth (SSoT)** architecture. Every file location must deterministically indicate the document's **Type**, **Lifecycle Stage**, and **Retention Policy**.

### 1.1. Active Workspaces (Hot Data)
| Directory | Purpose | Retention | Allowed Agents |
| :--- | :--- | :--- | :--- |
| **`communications/insights/`** | **Inbound Inbox**. Session logs, raw findings, and pre-merge analysis. | **Transient** (Move to Archive after session) | Gemini, Jules |
| **`design/3_work_artifacts/specs/`** | **Active Specs**. The "Blueprint" for current tasks. | **Active** (Until implementation complete) | Gemini (Spec) |
| **`design/3_work_artifacts/reports/active/`** | **Working Reports**. Drafts of audits or investigations. | **Active** | Gemini (Audit) |

### 1.2. The Canon (Cold Data / SSoT)
| Directory | Purpose | Retention | Immutability |
| :--- | :--- | :--- | :--- |
| **`design/1_governance/`** | **Constitution**. Architecture, Protocols, Roadmaps. | **Permanent** | High (Change via Proposal) |
| **`design/2_operations/ledgers/`** | **System State**. Tech Debt, Decisions, Reliability logs. | **Permanent** | Append-Only |
| **`design/3_work_artifacts/reports/`** | **Final Reports**. Completed audits, autopsy reports. | **Permanent** | High |

### 1.3. The Archive (Graveyard)
| Directory | Purpose | Structure |
| :--- | :--- | :--- |
| **`design/_archive/reports/{YYYY}/{MM}/`** | Old reports, completed handovers, obsolete insights. | Date-Sharded |
| **`design/_archive/specs/`** | Implemented or rejected specifications. | Flat |
| **`_internal/manuals/`** | **Agent Brain (Steering Tier)**. Specific instructions for Gemini workers (Spec, Review, Audit). | **Permanent / Self-Improving** |

### 1.4. Agent Steering Manuals (The Brain Area)
The `_internal/manuals/` directory contains the core "System Prompts" and behavioral guidelines for Gemini-cli 워커들입니다. 
-   **Role**: These are not just documentation, but **Steering Assets** that control AI output quality.
-   **Lifecycle**: During **Crystallization**, if current session insights reveal that Gemini or Jules failed due to a prompt ambiguity, the corresponding manual (e.g., `spec_writer.md`) MUST be updated.
-   **Security**: This directory is explicitly ignored by `.gitignore` to prevent leaking operational prompt engineering externally.

---

## 2. Filename Protocol (The "Penny Standard" for Files)

Files must be named using high-entropy, sortable patterns to prevent collisions and ambiguity.

-   **General Rule**: `[Type]-[YYYYMMDD]-[Slug].md`
-   **Specs**: `spec_[domain]_[feature_slug].md` (e.g., `spec_finance_liquidation_flow.md`)
-   **Reports**: `report_[YYYYMMDD]_[topic].md` (e.g., `report_20260215_tax_leak_analysis.md`)
-   **Insights**: `insight_[YYYYMMDD]_[short_desc].md` (e.g., `insight_20260215_circular_dependency.md`)

> **🚫 Forbidden**: `test.md`, `draft.md`, `temp.txt`, `notes.txt`. Generic names are strictly prohibited.

---

## 3. Template Standards

### 3.1. The Integrated Mission Guide (Spec)
*Usage: To define a task for Jules (Implementation).*

```markdown
# Mission Guide: [Mission Title]

## 1. Objectives
- [ ] Primary Goal (TD-ID)
- [ ] Secondary Goal

## 2. Reference Context
- [Protocol]: [[design/1_governance/architecture/standards/SEO_PATTERN.md]]
- [Related Spec]: [[design/3_work_artifacts/specs/spec_related.md]]

## 3. Implementation Roadmap
### Phase 1: Interface Definition
- Action: ...

### Phase 2: Logic Implementation
- Action: ...

## 4. Verification Plan
- **Command**: `pytest tests/module/test_target.py`
- **Success Criteria**: ...
```

### 3.2. The Insight Report
*Usage: To capture analysis results or architectural discoveries.*

```markdown
# Insight Report: [Topic]

## 1. Executive Summary
[Brief description of the finding or decision]

## 2. Detailed Analysis
- **Context**: ...
- **Evidence**: ...

## 3. Recommendations / Decisions
- [ ] Action Item 1
- [ ] Action Item 2

## 4. Metadata
- **Source**: [Agent Name/Session ID]
- **Date**: YYYY-MM-DD
```

---

## 4. Operational Protocols

### 4.1. The "God Folder" Prevention (Inbound Clearing)
The `cleanup-go.bat` or equivalent session-end process MUST:
1.  Scan `communications/insights/` for files older than the current session.
2.  Move valid reports to `design/_archive/reports/{YYYY}/{MM}/`.
3.  Delete empty or temporary files.
4.  **NEVER** leave files accumulating in `design/3_work_artifacts/reports/inbound/`.

### 4.2. Root Directory Purity
The root `reports/` directory is **DEPRECATED**.
-   **Action**: No new files allowed in `C:\coding\economics\reports\`.
-   **Migration**: Existing files in `reports/` must be moved to `design/3_work_artifacts/reports/` or `design/_archive/`.

### 4.3. Manifest Integrity
The `command_manifest.py` must only reference:
-   Specs located in `design/3_work_artifacts/specs/`.
-   Scripts located in `scripts/` or `_internal/scripts/`.
It must **never** reference a raw markdown file in `inbound/` as a mission guide.

---

## 5. Technical Debt Ledger Integration
Any deviation from this protocol (e.g., creating a file in root) is considered **Process Debt**.
-   **Detection**: Automated audits (like `audit_watchtower.py`) should flag file location violations.
-   **Resolution**: Immediate relocation to the correct canonical directory.

---

# 📝 Insight Report: Spec Doc Standardization

> **File Path**: `communications/insights/spec-doc-standardization.md`

## 1. Architectural Insights
### The "God Folder" Crisis
The directory `design/3_work_artifacts/reports/inbound/` has become a dumping ground for over 100+ heterogeneous files (PR reviews, audits, structural checks). This violates the **Single Responsibility Principle** at the directory level and breaks **Context Window Efficiency** for agents attempting to scan for relevant history.

### Source of Truth Fragmentation
We have active reports in the root `reports/` directory (e.g., `CORPORATE_TAX_REPORT.md`) and in `design/3_work_artifacts/reports/`. This split personality makes it impossible to define a canonical location for "System Health" data.

### The "Penny Standard" for Documentation
Just as we enforced integer-based math for finance, we must enforce **Strict Typed Locations** for documentation. A file's location must deterministically predict its lifecycle stage (Draft -> Active -> Archive) and its type (Spec, Report, Ledger).

## 2. Structural Decisions
1.  **Root Hygiene**: The `reports/` root directory is deprecated. All contents must be migrated to `design/3_work_artifacts/reports/` or archived.
2.  **Inbound Partitioning**: The `inbound` folder is deprecated in favor of a date-sharded archive strategy (`design/_archive/reports/YYYY/MM/`) and a transient `communications/insights/` inbox.
3.  **Template Enforcement**: New templates for `Mission Guide` and `Insight Report` are codified to ensure downstream agents (Jules) receive consistent context.

## 3. Verification Plan (Manual)
Since this is a structural policy change, "tests" are manual verification steps:
1.  Verify `design/1_governance/STANDARD_DOC_PROTOCOL.md` exists.
2.  Verify no new files are created in `reports/` root.
3.  Verify `command_manifest.py` points to the new protocol for future documentation missions.

## 4. Test Evidence
*N/A - This is a policy documentation task. No code changes to test.*