import subprocess
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
WORKER_SCRIPT = BASE_DIR / "scripts" / "gemini_worker.py"

def run_worker(worker_type, instruction, context_files=None, auto_run=False):
    cmd = ["python", str(WORKER_SCRIPT), worker_type, instruction]
    if context_files:
        cmd.extend(["--context"] + context_files)
    if auto_run:
        cmd.append("--auto-run")
    
    print(f"🏃 Running: {' '.join(cmd)}")
    return subprocess.run(cmd, text=True)

def main():
    print("🏁 Starting Session Checkpoint...")

    # 1. Git Commit
    print("\n📦 Step 1: Committing changes...")
    run_worker("git", "Commit all current changes with a meaningful message", auto_run=True)

    # 1.5 Consistency Guard (New)
    print("\n🛡️ Step 1.5: Consistency Guard (Roadmap vs Task)...")
    run_worker("verify", "Check if 'task.md' active tasks align with 'design/ROADMAP.md' phases. Output a warning if there is a mismatch.", context_files=["task.md", "design/ROADMAP.md"])

    # 2. Context Distillation & Routine Sync
    print("\n🧠 Step 2: Distilling context & Checking Registry...")
    context_files = [
        "design/project_status.md",
        "design/TECH_DEBT_LEDGER.md",
        "CHANGELOG.md",
        "task.md",
        "GEMINI.md"
    ]
    # Add implementation plan if exists
    if (BASE_DIR / "design" / "implementation_plan.md").exists():
        context_files.append("design/implementation_plan.md")
    
    run_worker("context", "Audit the Document Registry, synchronize project status, and generate a 20-line Warm Boot prompt for the next session.", context_files=context_files)

    # 3. Insight Accumulation
    print("\n🧐 Step 3: Accumulating Insights & Tech Debt...")
    drafts_dir = BASE_DIR / "design" / "drafts"
    recent_drafts = sorted(drafts_dir.glob("*.md"), key=os.path.getmtime, reverse=True)[:3]
    
    if recent_drafts:
        print(f"   Found {len(recent_drafts)} recent drafts. Merging into Ledger...")
        ledger_path = "design/TECH_DEBT_LEDGER.md"
        context_for_merge = [str(p.relative_to(BASE_DIR)) for p in recent_drafts]
        context_for_merge.append(ledger_path)
        
        instruction = (
            "Read the recent drafts and the Tech Debt Ledger. "
            "Extract any 'Insights' or 'Tech Debt' sections from the drafts and APPEND them to the Ledger "
            "in a structured format. Do not duplicate existing items. "
            "Output the FULL CONTENT of the updated Ledger."
        )
        
        # Updating helper call logic inline for now since run_worker signature is fixed above
        cmd = ["python", str(WORKER_SCRIPT), "context", instruction, "--output", ledger_path]
        cmd.extend(["--context"] + context_for_merge)
        subprocess.run(cmd, text=True)
    else:
        print("   No recent drafts found. Skipping accumulation.")

    # 3.5 Handover Report Auto-Gen (New)
    print("\n🤝 Step 3.5: Generating Handover Report...")
    handover_path = "communications/reports/HANDOVER.md"
    handover_instruction = (
        "Generate a 'End of Session Handover Report'. "
        "Summarize COMPLETED tasks from 'task.md', key code changes from 'CHANGELOG.md', "
        "and any new Tech Debt recorded. format as a professional handover document."
    )
    # Using 'context' worker to generate this report
    cmd = ["python", str(WORKER_SCRIPT), "context", handover_instruction, "--output", handover_path, "--context", "task.md", "CHANGELOG.md", "design/TECH_DEBT_LEDGER.md"]
    subprocess.run(cmd, text=True)

    # 4. Protocol Validation
    print("\n⚖️ Step 4: Running protocol validation for all changes...")
    run_worker("verify", "Perform a strict SoC and DTO compliance check on all recent changes.")

    print("\n✅ Checkpoint Complete. Warm Boot prompt generated in design/snapshots/latest_snapshot.md.")

if __name__ == "__main__":
    main()
