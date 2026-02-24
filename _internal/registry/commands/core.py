import sys
import json
import logging
from pathlib import Path
from _internal.registry.api import ICommand, CommandContext, CommandResult
from _internal.scripts.core.commands import run_command

logger = logging.getLogger(__name__)

class HarvestCommand(ICommand):
    @property
    def name(self) -> str:
        return "harvest"

    @property
    def description(self) -> str:
        return "Gathers reports and insights from the simulation."

    def execute(self, ctx: CommandContext) -> CommandResult:
        base_dir = ctx.base_dir
        weighted = base_dir / "_internal" / "scripts" / "weighted_harvester.py"
        target_script = weighted if weighted.exists() else base_dir / "_internal" / "scripts" / "report_harvester.py"
        
        cmd = [sys.executable, str(target_script)]
        res = run_command(cmd, cwd=base_dir)
        
        success = res is not None and res.returncode == 0
        return CommandResult(
            success=success,
            message="Harvest completed successfully" if success else "Harvest failed",
            exit_code=res.returncode if res else 1
        )

class SyncCommand(ICommand):
    @property
    def name(self) -> str:
        return "sync"

    @property
    def description(self) -> str:
        return "Synchronizes missions from manifest files into the persistent registry."

    def execute(self, ctx: CommandContext) -> CommandResult:
        sp = ctx.service_provider
        gemini_service = sp.get_gemini_service()
        jules_service = sp.get_jules_service()
        
        g_count = gemini_service.migrate_from_registry_dir()
        j_count = jules_service.migrate_from_registry_dir()
        
        total = g_count + j_count
        return CommandResult(
            success=True,
            message=f"Sync complete. Migrated {total} missions.",
            data={"gemini_count": g_count, "jules_count": j_count}
        )

class ResetCommand(ICommand):
    @property
    def name(self) -> str:
        return "reset"

    @property
    def description(self) -> str:
        return "Resets manifest and registry files to factory defaults."

    def execute(self, ctx: CommandContext) -> CommandResult:
        print("🧹 Resetting JSON registries (manifests are preserved)...")
        
        # Reset JSON Registries only
        empty_reg = {"_meta": {"version": "1.0"}, "missions": {}}
        for reg_path in [ctx.gemini_registry_json, ctx.jules_registry_json]:
            reg_path.write_text(json.dumps(empty_reg, indent=2), encoding='utf-8')
            lock = reg_path.with_suffix('.lock')
            if lock.exists():
                lock.unlink()
            print(f"  🗑️ Cleared: {reg_path.name}")

        # Remove legacy files
        legacy_files = [
            ctx.base_dir / "_internal" / "registry" / "command_registry.json",
            ctx.base_dir / "_internal" / "registry" / "mission_db.json"
        ]
        for f in legacy_files:
            if f.exists():
                f.unlink()
                print(f"  🗑️ Removed legacy: {f.name}")

        print("ℹ️ Manifest files (.py) were NOT touched. Use them to re-arm missions.")
        return CommandResult(success=True, message="JSON registry reset complete. Manifests preserved.")
