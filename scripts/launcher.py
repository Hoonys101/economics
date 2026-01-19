import sys
import os
import json
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
REGISTRY_PATH = BASE_DIR / "design" / "command_registry.json"

def load_registry():
    if not REGISTRY_PATH.exists():
        print(f"❌ Registry not found at {REGISTRY_PATH}")
        sys.exit(1)
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def run_command(cmd_list, capture_output=False):
    """Executes a command list securely."""
    print(f"🚀 Executing: {' '.join(cmd_list)}")
    try:
        result = subprocess.run(cmd_list, cwd=BASE_DIR, capture_output=capture_output, text=True, encoding='utf-8', shell=False)
        if result.returncode != 0:
            print(f"❌ Command failed with return code {result.returncode}")
            if result.stderr:
                print(result.stderr)
        return result
    except Exception as e:
        print(f"❌ Execution error: {e}")
        return None

def run_gemini(args, registry):
    data = registry.get("gemini", {})
    worker = data.get("worker", "spec")
    instruction = data.get("instruction", "")
    context = data.get("context", [])
    output = data.get("output", "")
    output = data.get("output", "")
    audit = data.get("audit", "")
    model = data.get("model", "")

    cmd = [sys.executable, str(BASE_DIR / "scripts" / "gemini_worker.py"), worker, instruction]
    if context:
        cmd.extend(["-c"] + context)
    if output:
        cmd.extend(["-o", output])
    if audit:
        cmd.extend(["-a", audit])
    if model:
        cmd.extend(["--model", model])
    
    run_command(cmd)

def run_jules(args, registry):
    data = registry.get("jules", {})
    command = data.get("command", "list-sessions")
    session_id = data.get("session_id", "")
    title = data.get("title", "")
    instruction = data.get("instruction", "")
    file_path = data.get("file", "")
    wait = data.get("wait", False)

    cmd = [sys.executable, str(BASE_DIR / "scripts" / "jules_bridge.py"), command]

    if command == "create":
        cmd.append(title)
        if file_path:
            cmd.extend(["-f", file_path])
        else:
            cmd.append(instruction)
    elif command == "send-message":
        if not session_id:
            print("❌ Error: session_id is required for send-message")
            return
        cmd.append(session_id)
        if file_path:
            cmd.extend(["-f", file_path])
        else:
            cmd.append(instruction)
    elif command in ["complete", "get-session"]:
        if not session_id:
            print(f"❌ Error: session_id is required for {command}")
            return
        cmd.append(session_id)
    
    if wait:
        cmd.append("--wait")
    
    # Redirect output for Jules as in the bat files
    output_log = BASE_DIR / "communications" / "jules_logs" / "last_run.md"
    output_log.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 Executing Jules Bridge: {command}...")
    with open(output_log, "w", encoding="utf-8") as f:
        try:
            # We use subprocess.Popen or run with stdout redirection
            result = subprocess.run(cmd, cwd=BASE_DIR, stdout=f, stderr=f, text=True, shell=True)
            if result.returncode == 0:
                print(f"✅ Success! Log: {output_log}")
            else:
                print(f"❌ Failed! Check: {output_log}")
        except Exception as e:
            print(f"❌ Error: {e}")

def run_git_review(args, registry):
    data = registry.get("git_review", {})
    branch = args[0] if args else data.get("branch", "main")
    instruction = args[1] if len(args) > 1 else data.get("instruction", "Analyze this PR.")

    print(f"🔍 [Git-Review] Syncing and analyzing branch: {branch}")
    
    # 1. Get latest commit
    sync_cmd = [sys.executable, str(BASE_DIR / "scripts" / "git_sync_checker.py"), branch]
    res = run_command(sync_cmd, capture_output=True)
    if not res or not res.stdout.strip():
        print("❌ Failed to get latest commit.")
        return
    
    commit_hash = res.stdout.strip().split('\n')[-1] # Take the last line
    print(f"📍 Target Commit: {commit_hash}")

    # 2. Generate Diff
    short_name = branch.split('/')[-1]
    diff_file = BASE_DIR / "design" / "gemini_output" / f"pr_diff_{short_name}.txt"
    diff_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"📝 Generating diff for {branch}...")
    with open(diff_file, "w", encoding="utf-8") as f:
        subprocess.run(["git", "diff", f"main..{commit_hash}"], cwd=BASE_DIR, stdout=f, shell=True)

    # 3. Gemini Review
    review_output = BASE_DIR / "design" / "gemini_output" / f"pr_review_{short_name}.md"
    gemini_cmd = [
        sys.executable, 
        str(BASE_DIR / "scripts" / "gemini_worker.py"), 
        "git-review", 
        instruction, 
        "-c", str(diff_file)
    ]
    
    print("🧠 Running AI Code Review...")
    with open(review_output, "w", encoding="utf-8") as f:
        subprocess.run(gemini_cmd, cwd=BASE_DIR, stdout=f, stderr=f, shell=True)
    
    print(f"✅ Review complete. Report: {review_output}")

def run_merge(args, registry):
    data = registry.get("merge", {})
    branch = args[0] if args else data.get("branch", "")
    if not branch:
        print("❌ Error: Branch name required for merge.")
        return

    commands = [
        ["git", "checkout", "main"],
        ["git", "pull", "origin", "main"],
        ["git", "ls-remote", "--exit-code", "--heads", "origin", branch],
        ["git", "merge", f"origin/{branch}", "--no-edit"],
        ["git", "push", "origin", "main"],
        ["git", "push", "origin", "--delete", branch]
    ]

    for cmd in commands:
        res = run_command(cmd)
        if res.returncode != 0:
            print(f"❌ Stop: Merge sequence interrupted at '{' '.join(cmd)}'")
            return
    print(f"✅ Branch {branch} successfully merged and cleaned up.")

def run_harvest(args, registry):
    cmd = [sys.executable, str(BASE_DIR / "scripts" / "report_harvester.py")]
    run_command(cmd)

def main():
    if len(sys.argv) < 2:
        print("Usage: launcher.py <tool> [args...]")
        sys.exit(1)

    tool = sys.argv[1]
    extra_args = sys.argv[2:]
    registry = load_registry()

    dispatch = {
        "gemini": run_gemini,
        "jules": run_jules,
        "git-review": run_git_review,
        "merge": run_merge,
        "harvest": run_harvest
    }

    if tool in dispatch:
        dispatch[tool](extra_args, registry)
    else:
        print(f"❌ Unknown tool: {tool}")
        sys.exit(1)

if __name__ == "__main__":
    main()
