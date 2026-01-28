import subprocess
import os
import re
from typing import List, Set

# Configuration
BRANCH_PATTERNS = ["refactor-*", "observer-*", "audit-*", "structural-*", "parity-*", "economic-*", "*-action-plan-*", "*-proposal-*", "wo-*"]
REPORT_DIRS = ["design/3_work_artifacts/reports/", "design/_archive/gemini_output/", "reports/"]
LOCAL_STORAGE_DIR = "design/3_work_artifacts/reports/inbound/"
LOG_FILE = "design/2_operations/ledgers/INBOUND_REPORTS.md"

def run_command(cmd: List[str]) -> str:
    try:
        # Windows encoding issue: force utf-8 for git output
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding="utf-8")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e.stderr}")
        return ""
    except Exception as e:
        print(f"Unexpected error: {e}")
        return ""

def get_remote_branches() -> List[str]:
    print("[Harvester] Fetching remote branches...")
    run_command(["git", "fetch", "origin"])
    branches_raw = run_command(["git", "branch", "-r"])
    branches = []
    for line in branches_raw.split("\n"):
        branch = line.strip()
        if not branch or "->" in branch:
            continue
        # Remove 'origin/' prefix for pattern matching but keep it for git commands
        clean_name = branch.replace("origin/", "")
        for pattern in BRANCH_PATTERNS:
            # WO-106 FIX: Support both '-' and '/' in branch names
            regex = pattern.replace("*", ".*").replace("-", "[-/]")
            if re.match(f"^{regex}$", clean_name):
                branches.append(branch)
                break
    return list(set(branches))

def get_new_files_in_branch(branch: str) -> List[str]:
    # Use 'git diff origin/main...branch' to get only files changed/added in this branch relative to main
    cmd = ["git", "diff", "origin/main..." + branch, "--name-only"]
    files_raw = run_command(cmd)
    if not files_raw:
        return []
    
    found_files = []
    lines = files_raw.split("\n")
    for line in lines:
        line = line.strip()
        if not line.endswith(".md"):
            continue
        # Check if file belongs to any of the monitored directories
        if any(line.startswith(d) for d in REPORT_DIRS):
            found_files.append(line)
    return found_files

def clean_branch_name(name: str) -> str:
    """Removes common prefixes to keep the harvested filename short and relevant."""
    name = name.lower()
    prefixes = ["origin/", "audit-", "wo-105-", "wo-"]
    for p in prefixes:
        if name.startswith(p):
            name = name[len(p):]
    return name.replace("/", "_")

def harvest():
    if not os.path.exists(LOCAL_STORAGE_DIR):
        os.makedirs(LOCAL_STORAGE_DIR)
        print(f"[Harvester] Created directory {LOCAL_STORAGE_DIR}")

    branches = get_remote_branches()
    print(f"[Harvester] Found {len(branches)} matching branches.")

    new_files_count = 0
    harvested_log = []

    for branch in branches:
        branch_id = branch.replace("origin/", "")
        display_name = clean_branch_name(branch_id)
        files = get_new_files_in_branch(branch)
        
        for file_path in files:
            file_name = os.path.basename(file_path)
            # Safe filename: [cleaned_branch]_[filename]
            safe_name = f"{display_name}_{file_name}"
            target_path = os.path.join(LOCAL_STORAGE_DIR, safe_name)

            if not os.path.exists(target_path):
                print(f"[Harvester] New report found in {branch_id}: {file_name}")
                content = run_command(["git", "show", f"{branch}:{file_path}"])
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(content)
                new_files_count += 1
                harvested_log.append(f"- **{file_name}** (from `{branch_id}`) -> `{safe_name}`")

    if new_files_count > 0:
        print(f"[Harvester] Successfully harvested {new_files_count} new reports.")
        update_log(harvested_log)
    else:
        print("[Harvester] No new reports found.")

def update_log(new_entries: List[str]):
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    header = f"\n## Harvested on {timestamp}\n"
    content = "\n".join(new_entries) + "\n"
    
    file_exists = os.path.exists(LOG_FILE)
    mode = "a" if file_exists else "w"
    
    with open(LOG_FILE, mode, encoding="utf-8") as f:
        if not file_exists:
            f.write("# Inbound Reports Log\n")
        f.write(header)
        f.write(content)
    print(f"[Harvester] Updated {LOG_FILE}")

if __name__ == "__main__":
    harvest()
