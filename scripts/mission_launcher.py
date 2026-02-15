"""
Mission Launcher Script.
Replaces the legacy launcher.py with a robust, service-backed implementation.
"""
import argparse
import sys
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from _internal.registry.api import MissionDTO, MissionType
from _internal.registry.service import MissionRegistryService

def list_missions(service: MissionRegistryService):
    missions = service.load_missions()
    if not missions:
        print("No missions found.")
        return

    print(f"{'KEY':<20} {'TYPE':<10} {'TITLE'}")
    print("-" * 60)
    for key, m in missions.items():
        print(f"{key:<20} {m.type.value:<10} {m.title}")

def create_mission(service: MissionRegistryService, args):
    mission_type = MissionType.GEMINI if args.type == "gemini" else MissionType.JULES

    dto = MissionDTO(
        key=args.key,
        title=args.title,
        type=mission_type,
        instruction_raw=args.instruction,
        worker=args.worker,
        output_path=args.output,
        command=args.command
    )

    if args.context:
        dto.context_files = args.context

    service.register_mission(dto)
    print(f"Mission '{args.key}' created.")

def run_mission(service: MissionRegistryService, key: str):
    mission = service.get_mission(key)
    if not mission:
        print(f"Error: Mission '{key}' not found.")
        sys.exit(1)

    prompt = service.get_mission_prompt(key)
    print("=== MISSION PROMPT ===")
    print(prompt)
    print("======================")

    # In a real launcher, this would dispatch to an agent.
    # Here we just output the prompt as per the spec "get_mission_prompt".

def delete_mission(service: MissionRegistryService, key: str):
    if service.delete_mission(key):
        print(f"Mission '{key}' deleted.")
    else:
        print(f"Mission '{key}' not found.")

def main():
    parser = argparse.ArgumentParser(description="Mission Registry Launcher")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # LIST
    subparsers.add_parser("list", help="List all missions")

    # CREATE
    create_parser = subparsers.add_parser("create", help="Register a new mission")
    create_parser.add_argument("key", help="Unique mission key")
    create_parser.add_argument("--type", choices=["jules", "gemini"], required=True)
    create_parser.add_argument("--title", required=True)
    create_parser.add_argument("--instruction", required=True)
    create_parser.add_argument("--worker", help="Worker type (Gemini only)")
    create_parser.add_argument("--output", help="Output path (Gemini only)")
    create_parser.add_argument("--command", help="Command (Jules only)")
    create_parser.add_argument("--context", nargs="*", help="Context files")

    # RUN
    run_parser = subparsers.add_parser("run", help="Run (print prompt) for a mission")
    run_parser.add_argument("key", help="Mission key")

    # DELETE
    delete_parser = subparsers.add_parser("delete", help="Delete a mission")
    delete_parser.add_argument("key", help="Mission key")

    # MIGRATE
    migrate_parser = subparsers.add_parser("migrate", help="Migrate from legacy manifest")
    migrate_parser.add_argument("path", help="Path to legacy command_manifest.py")

    args = parser.parse_args()
    service = MissionRegistryService()

    if args.command == "list":
        list_missions(service)
    elif args.command == "create":
        create_mission(service, args)
    elif args.command == "run":
        run_mission(service, args.key)
    elif args.command == "delete":
        delete_mission(service, args.key)
    elif args.command == "migrate":
        count = service.migrate_from_legacy(args.path)
        print(f"Migrated {count} missions.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
