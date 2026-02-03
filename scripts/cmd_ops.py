import sys
import json
import os
import argparse
from pathlib import Path

# Config
BASE_DIR = Path(__file__).parent.parent
REGISTRY_PATH = BASE_DIR / "design" / "command_registry.json"

def load_registry():
    if not REGISTRY_PATH.exists():
        return {"_meta": {"updated": "new"}}
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ JSON Load Error: {e}")
        return {}

def save_registry(data):
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Registry Updated: {REGISTRY_PATH}")

def op_set_gemini(args):
    data = load_registry()
    
    entry = {
        "title": args.title,
        "worker": args.worker,
        "instruction": args.instruction
    }
    
    if args.context:
        entry["context"] = args.context
    if args.output:
        entry["output"] = args.output
    if args.model:
        entry["model"] = args.model
        
    data[args.key] = entry
    save_registry(data)

MANDATORY_REPORTING_PROMPT = "\n\n🚨 [MANDATORY] 작업 완료 전, 발견된 기술 부채와 인사이트를 'communications/insights/[MissionKey].md' 파일에 반드시 기록하십시오. (No Report = No Merge)"

def op_set_jules(args):
    data = load_registry()
    
    instruction = args.instruction
    if args.command == "create":
        # Auto-append reporting protocol for new coding sessions
        if MANDATORY_REPORTING_PROMPT not in instruction:
            instruction += MANDATORY_REPORTING_PROMPT

    entry = {
        "title": args.title,
        "command": args.command,
        "instruction": instruction
    }
    
    if args.file:
        entry["file"] = args.file
    if args.session_id:
        entry["session_id"] = args.session_id
    if args.wait:
        entry["wait"] = True
        
    data[args.key] = entry
    save_registry(data)

def op_delete(args):
    data = load_registry()
    if args.key in data:
        del data[args.key]
        print(f"🗑️ Deleted key: {args.key}")
        save_registry(data)
    else:
        print(f"⚠️ Key not found: {args.key}")

def op_reset(args):
    """Resets the registry to a clean state using the template."""
    import shutil
    template_path = "design/clean_registry_template.json"
    registry_path = "design/command_registry.json"
    
    try:
        shutil.copy(template_path, registry_path)
        print(f"🧹 Registry Reset Complete: {registry_path} is now clean.")
    except FileNotFoundError:
        print("❌ Template file not found. Creating a minimal one...")
        data = {
            "_meta": {
                "session": "Reset Fallback",
                "updated": "2026-01-30",
                "author": "System"
            }
        }
        save_registry(data)
        print("🧹 Registry Reset Complete (Fallback Mode).")

def main():
    parser = argparse.ArgumentParser(description="Command Registry Operations")
    subparsers = parser.add_subparsers(dest="operation", required=True)
    
    # Set Gemini
    p_gemini = subparsers.add_parser("set-gemini", help="Set a Gemini mission")
    p_gemini.add_argument("key", help="Mission Key")
    p_gemini.add_argument("--title", "-t", required=True, help="Mission Title")
    p_gemini.add_argument("--worker", required=True, choices=["audit", "spec", "git-review", "context", "verify", "git", "reporter"], help="Worker type")
    p_gemini.add_argument("--instruction", "-i", required=True, help="Instruction")
    p_gemini.add_argument("--context", nargs="+", help="Context files")
    p_gemini.add_argument("--output", help="Output file")
    p_gemini.add_argument("--model", default="gemini-2.5-pro", help="Model Override (default: gemini-2.5-pro)")
    
    # Set Jules
    p_jules = subparsers.add_parser("set-jules", help="Set a Jules mission")
    p_jules.add_argument("key", help="Mission Key")
    p_jules.add_argument("--title", "-t", required=True, help="Mission Title")
    p_jules.add_argument("--command", required=True, choices=["create", "send-message"], help="Command Type")
    p_jules.add_argument("--instruction", "-i", required=True, help="Instruction")
    p_jules.add_argument("--file", help="Target File")
    p_jules.add_argument("--session_id", help="Session ID")
    p_jules.add_argument("--wait", action="store_true", help="Wait for completion")

    # Delete
    p_del = subparsers.add_parser("del", help="Delete a mission")
    p_del.add_argument("key", help="Mission Key")

    # Reset (New)
    p_reset = subparsers.add_parser("reset", help="Reset registry to clean state")

    args = parser.parse_args()
    
    if args.operation == "set-gemini":
        op_set_gemini(args)
    elif args.operation == "set-jules":
        op_set_jules(args)
    elif args.operation == "del":
        op_delete(args)
    elif args.operation == "reset":
        op_reset(args)

if __name__ == "__main__":
    main()
