# [Refactor Plan] Documentation Hierarchy Consolidation

This plan addresses the risks identified in the pre-flight audit by restructuring the `design` directory for clarity and maintainability.

---

## 1. Proposed Directory Structure (`/design`)

The new structure centralizes entry points and groups related documents into logical subdirectories, following an "Abstract -> Concrete" flow.

```
/design
├── INDEX.md
├── QUICKSTART.md
├── archives/
│   └── TECHNICAL_DEBT.md
├── kb/
│   ├── COMMAND_REGISTRY_REFERENCE.md
│   ├── ECONOMIC_INSIGHTS.md
│   ├── RELIABILITY_LEDGER.md
│   └── TROUBLESHOOTING.md
├── manuals/
│   ├── GIT_REVIEWER.md
│   ├── JULES_DOC_GUIDE.md
│   ├── REPORTER.md
│   ├── SPEC_WRITER.md
│   └── VALIDATOR.md
├── protocols/
│   ├── PROTOCOL_ENGINEERING.md
│   ├── PROTOCOL_GOVERNANCE.md
│   └── PROTOCOL_TOOLING.md
├── status/
│   ├── DEBT_REPAYMENT_PLAN_v2.md
│   ├── PLATFORM_ARCHITECTURE.md
│   ├── PROJECT_STATUS.md
│   ├── ROADMAP.md
│   ├── TECH_DEBT_LEDGER.md
│   └── handovers/
└── ... (other existing folders like specs/, work_orders/, etc.)
```

---

## 2. PowerShell Migration Script

This script will atomically create the new directory structure and move the existing files. **Execute this script from within the `design` directory.**

```powershell
# [CRITICAL] This script MUST be run from inside the 'C:\coding\economics\design' directory.

# Step 1: Create the new directory structure
Write-Host "Creating new directory structure..."
$dirs = @("status", "protocols", "manuals", "kb", "archives")
foreach ($dir in $dirs) {
    if (-not (Test-Path -Path $dir)) {
        New-Item -ItemType Directory -Path $dir
        Write-Host " -> Created directory: $dir"
    } else {
        Write-Host " -> Directory already exists: $dir"
    }
}

# Step 2: Define file-to-directory mappings
$fileMappings = @{
    # Status & Roadmaps
    "PROJECT_STATUS.md" = "status";
    "platform_architecture.md" = "status";
    "ROADMAP.md" = "status"; # Assuming ROADMAP.md exists at the root
    "TECH_DEBT_LEDGER.md" = "status";
    "DEBT_REPAYMENT_PLAN_v2.md" = "status";
    # Protocols
    "PROTOCOL_TOOLING.md" = "protocols";
    "PROTOCOL_ENGINEERING.md" = "protocols";
    "PROTOCOL_GOVERNANCE.md" = "protocols";
    # Manuals
    "spec_writer.md" = "manuals";
    "git_reviewer.md" = "manuals";
    "reporter.md" = "manuals";
    "validator.md" = "manuals";
    "JULES_DOCUMENTATION_GUIDE.md" = "manuals";
    # Knowledge Base
    "TROUBLESHOOTING.md" = "kb";
    "COMMAND_REGISTRY_REFERENCE.md" = "kb";
    "ECONOMIC_INSIGHTS.md" = "kb";
    "RELIABILITY_LEDGER.md" = "kb";
    # Archives (for orphaned files)
    "TECHNICAL_DEBT.md" = "archives";
}

# Step 3: Move files to their new locations
Write-Host "Moving files..."
foreach ($file in $fileMappings.Keys) {
    $destination = $fileMappings[$file]
    if (Test-Path -Path $file) {
        Move-Item -Path $file -Destination $destination -Force
        Write-Host " -> Moved '$file' to '$destination/'"
    } else {
        Write-Warning " -> File not found, skipping: $file"
    }
}

# Step 4: Move existing directories
Write-Host "Moving directories..."
if (Test-Path -Path "handovers") {
    Move-Item -Path "handovers" -Destination "status/" -Force
    Write-Host " -> Moved 'handovers/' to 'status/'"
}

Write-Host "File migration complete."
Write-Warning "CRITICAL NEXT STEP: You must now update the internal hyperlinks within all moved Markdown files to reflect the new paths. The provided 'INDEX.md' is already updated, but other files are not."

```

---

## 3. New `design/INDEX.md` Content

Replace the content of `design/INDEX.md` with the following. The links are updated to match the new, clean structure.

```markdown
# Documentation Index

Welcome to the Economics Simulation Project. This index maps our documentation into three main categories: **Protocols**, **Status/Roadmaps**, and **Worker Manuals**.

---

## 🚀 1. Start Here
- **[QUICKSTART.md](QUICKSTART.md)**: **The entry point**. If you are lost, start here.

---

## 🚦 2. Status & Roadmaps
Current progress and the technical context of the simulation.
- **[PROJECT_STATUS.md](status/PROJECT_STATUS.md)**: Current build status and next tasks.
- **[ROADMAP.md](status/ROADMAP.md)**: The long-term architectural vision.
- **[TECH_DEBT_LEDGER.md](status/TECH_DEBT_LEDGER.md)**: Unresolved debts and remediation plans.
- **[DEBT_REPAYMENT_PLAN_v2.md](status/DEBT_REPAYMENT_PLAN_v2.md)**: **Current priority** (Abstraction Wall & Cleanup).
- **[Handover Documents](status/handovers/)**: Context from previous work sessions.
- **[Platform Architecture](status/platform_architecture.md)**: High-level system design.

---

## 🏛️ 3. Core Protocols
Universal rules for all agents and contributors.
- **[PROTOCOL_TOOLING.md](protocols/PROTOCOL_TOOLING.md)**: How to use the SCR tools (Gemini, Jules, etc.).
- **[PROTOCOL_ENGINEERING.md](protocols/PROTOCOL_ENGINEERING.md)**: Architectural standards (SoC, DTO, Sacred Sequence).
- **[PROTOCOL_GOVERNANCE.md](protocols/PROTOCOL_GOVERNANCE.md)**: Roles, PR reviews, and session cleanup.

---

## 🤖 4. Specialized Worker Manuals
Deep-dive instructions for specific AI workers and specialized tasks.
- **[SPEC_WRITER.md](manuals/spec_writer.md)**: How to write high-quality technical specs.
- **[GIT_REVIEWER.md](manuals/git_reviewer.md)**: Security and integrity audit pillars for PRs.
- **[REPORTER.md](manuals/reporter.md)**: Summarizing session results and leaks.
- **[VALIDATOR.md](manuals/validator.md)**: Strict rule-checking for architecture.
- **[JULES_DOC_GUIDE.md](manuals/JULES_DOCUMENTATION_GUIDE.md)**: Populating empty specs from code analysis.

---

## 🆘 5. Knowledge Base
- **[TROUBLESHOOTING.md](kb/TROUBLESHOOTING.md)**: Common errors and solutions.
- **[COMMAND_REGISTRY_REFERENCE.md](kb/COMMAND_REGISTRY_REFERENCE.md)**: Deep dive into the SCR JSON schema.
- **[ECONOMIC_INSIGHTS.md](kb/ECONOMIC_INSIGHTS.md)**: Domain knowledge discovered during runtime.
- **[RELIABILITY_LEDGER.md](kb/RELIABILITY_LEDGER.md)**: System stability metrics.
```
