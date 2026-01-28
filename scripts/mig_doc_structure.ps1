# SCRIPT: Restructure the /design directory

# --- CONFIGURATION ---
$ErrorActionPreference = "Stop"
$designDir = ".\design"
Write-Host "INFO: Starting restructuring of '$designDir'..."

# --- 1. DEFINE NEW DIRECTORY STRUCTURE ---
$l1_governance = "$designDir\1_governance"
$l2_operations = "$designDir\2_operations"
$l3_artifacts = "$designDir\3_work_artifacts"
$archive = "$designDir\_archive"

$ledgersDir = "$l2_operations\ledgers"

$newDirs = @(
    $l1_governance,
    $l2_operations,
    $l3_artifacts,
    $archive,
    $ledgersDir
)

# --- 2. CREATE NEW DIRECTORIES ---
Write-Host "INFO: Creating new directory structure..."
foreach ($dir in $newDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "  [+] Created: $dir"
    } else {
        Write-Host "  [~] Exists:  $dir"
    }
}

# --- 3. MOVE ROOT-LEVEL FILES ---
Write-Host "INFO: Moving root-level markdown files..."
# Check if files exist before moving to avoid errors
if (Test-Path "$designDir\platform_architecture.md") {
    Move-Item -Path "$designDir\platform_architecture.md" -Destination $l1_governance -Force
    Write-Host "  [->] Moved platform_architecture.md to 1_governance"
}
if (Test-Path "$designDir\project_structure.md") {
    Move-Item -Path "$designDir\project_structure.md" -Destination $l1_governance -Force
    Write-Host "  [->] Moved project_structure.md to 1_governance"
}
if (Test-Path "$designDir\project_status.md") {
    Move-Item -Path "$designDir\project_status.md" -Destination $l1_governance -Force
    Write-Host "  [->] Moved project_status.md to 1_governance"
}

if (Test-Path "$designDir\TECHNICAL_DEBT.md") {
    Move-Item -Path "$designDir\TECHNICAL_DEBT.md" -Destination $ledgersDir -Force
    Write-Host "  [->] Moved TECHNICAL_DEBT.md to 2_operations/ledgers"
}
if (Test-Path "$designDir\TECH_DEBT_LEDGER.md") {
    Move-Item -Path "$designDir\TECH_DEBT_LEDGER.md" -Destination $ledgersDir -Force
    Write-Host "  [->] Moved TECH_DEBT_LEDGER.md to 2_operations/ledgers"
}

# --- 4. MOVE EXISTING FOLDERS ---
Write-Host "INFO: Moving existing directories into new structure..."

# Helper function to move dir if exists
function Move-Dir-Safe {
    param($src, $dest)
    if (Test-Path $src) {
        Move-Item -Path $src -Destination $dest -Force
        Write-Host "  [->] Moved $src to $dest"
    } else {
        Write-Host "  [!] Skipped: $src (Not Found)"
    }
}

# Layer 1
Move-Dir-Safe "$designDir\protocols" $l1_governance

# Layer 2
Move-Dir-Safe "$designDir\manuals" $l2_operations
Move-Dir-Safe "$designDir\roles" $l2_operations
Move-Dir-Safe "$designDir\templates" $l2_operations

# Handle ledgers specially (merge if needed, but here we just moved files into it)
# We already populated $ledgersDir with files, but if there was a ledgers/ folder before, move its content
if (Test-Path "$designDir\ledgers") {
    Get-ChildItem -Path "$designDir\ledgers" | Move-Item -Destination $ledgersDir -Force
    Remove-Item -Path "$designDir\ledgers" -Force -Recurse
    Write-Host "  [->] Integrated old ledgers/ folder into new structure"
}

# Layer 3
Move-Dir-Safe "$designDir\specs" $l3_artifacts
Move-Dir-Safe "$designDir\work_orders" $l3_artifacts
Move-Dir-Safe "$designDir\audits" $l3_artifacts
if (Test-Path "$designDir\REPORTS") {
    Move-Item -Path "$designDir\REPORTS" -Destination "$l3_artifacts\reports" -Force
    Write-Host "  [->] Moved REPORTS/ to 3_work_artifacts/reports"
}
Move-Dir-Safe "$designDir\drafts" $l3_artifacts
Move-Dir-Safe "$designDir\test_plans" $l3_artifacts
Move-Dir-Safe "$designDir\test_reports" $l3_artifacts

# Archive
Move-Dir-Safe "$designDir\gemini_output" $archive
Move-Dir-Safe "$designDir\handovers" $archive
Move-Dir-Safe "$designDir\snapshots" $archive
Move-Dir-Safe "$designDir\feedback" $archive
Move-Dir-Safe "$designDir\requests" $archive

Write-Host "SUCCESS: Directory restructuring complete."
