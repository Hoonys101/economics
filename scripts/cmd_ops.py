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

def op_set_jules(args):
    data = load_registry()
    
    entry = {
        "command": args.command,
        "instruction": args.instruction
    }
    
    if args.title:
        entry["title"] = args.title
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

def main():
    parser = argparse.ArgumentParser(description="Command Registry Operations")
    subparsers = parser.add_subparsers(dest="op", required=True)
    
    # 1. Set Gemini Mission
    p_gem = subparsers.add_parser("set-gemini", help="Add/Update Gemini Mission")
    p_gem.add_argument("key", help="Mission Key (Menu Title)")
    p_gem.add_argument("--worker", required=True, choices=["audit", "spec", "git-review", "context", "verify"], help="Worker Type")
    p_gem.add_argument("--instruction", "-i", required=True, help="Instruction Prompt")
    p_gem.add_argument("--context", "-c", nargs="+", help="Context Files")
    p_gem.add_argument("--output", "-o", help="Output File Path")
    p_gem.add_argument("--model", "-m", help="Gemini Model")

    # 2. Set Jules Mission
    p_jul = subparsers.add_parser("set-jules", help="Add/Update Jules Mission")
    p_jul.add_argument("key", help="Mission Key")
    p_jul.add_argument("--command", required=True, choices=["create", "send-message"], help="Command Type")
    p_jul.add_argument("--instruction", "-i", required=True, help="Instruction Prompt")
    p_jul.add_argument("--title", "-t", help="Task Title (for create)")
    p_jul.add_argument("--file", "-f", help="Attributes File Injection")
    p_jul.add_argument("--session_id", "-s", help="Active Session ID for send-message")
    p_jul.add_argument("--wait", action="store_true", help="Wait for completion")

    # 3. Delete Mission
    p_del = subparsers.add_parser("del", help="Delete Mission")
    p_del.add_argument("key", help="Mission Key to delete")

    args = parser.parse_args()
    
    if args.op == "set-gemini":
        op_set_gemini(args)
    elif args.op == "set-jules":
        op_set_jules(args)
    elif args.op == "del":
        op_delete(args)

if __name__ == "__main__":
    main()
