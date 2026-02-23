import sys
import subprocess
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from _internal.registry.api import ICommand, CommandContext, CommandResult, MissionType
from _internal.scripts.core.commands import run_command
from _internal.scripts.core.context import resolve_manual_links, get_core_contract_paths

logger = logging.getLogger(__name__)

class GeminiDispatcher(ICommand):
    @property
    def name(self) -> str:
        return "gemini"

    @property
    def description(self) -> str:
        return "Dispatches a dynamic Gemini mission."

    def execute(self, ctx: CommandContext) -> CommandResult:
        if not ctx.raw_args:
            interactive_script = ctx.base_dir / "_internal" / "scripts" / "run_gemini_interactive.py"
            if interactive_script.exists():
                print("🚀 Entering Interactive Gemini Command Center...")
                subprocess.run([sys.executable, str(interactive_script)], cwd=ctx.base_dir)
                return CommandResult(success=True, message="Interactive session closed.")

        key = ctx.raw_args[0]
        service = ctx.service_provider.get_gemini_service()
        
        # Auto-sync before execution
        service.migrate_from_registry_dir()
        
        mission = service.get_mission(key)
        if not mission:
            msg = f"❌ Error: Key '{key}' not found in Gemini registry."
            print(msg)
            return CommandResult(success=False, message=msg)
        
        if mission.type != MissionType.GEMINI:
            msg = f"❌ Error: Mission '{key}' is not a Gemini mission."
            print(msg)
            return CommandResult(success=False, message=msg)

        instruction = service.get_mission_prompt(key)
        
        from _internal.registry.mission_protocol import WORKER_MODEL_MAP
        model = mission.model or WORKER_MODEL_MAP.get(mission.worker, "gemini-3-flash-preview")

        output_path = mission.output_path
        if not output_path:
            mapping = {
                "spec": f"gemini-output/spec/MISSION_{key}_SPEC.md",
                "audit": f"gemini-output/audit/MISSION_{key}_AUDIT.md",
                "reporter": f"gemini-output/audit/MISSION_{key}_AUDIT.md",
                "reviewer": f"gemini-output/review/MISSION_{key}_REVIEW.md",
                "crystallizer": f"gemini-output/insight/CRYSTAL_{key}.md"
            }
            output_path = mapping.get(mission.worker)

        from _internal.scripts.core.context_injector.service import ContextInjectorService
        from modules.tools.context_injector.api import InjectionRequestDTO
        
        injector = ContextInjectorService()
        existing_context = mission.context_files or []
        
        req = InjectionRequestDTO(
            target_files=existing_context,
            include_tests=True,
            include_docs=True,
            max_dependency_depth=1
        )
        
        injection_result = injector.analyze_context(req)
        final_context = list(set(existing_context + [node.file_path for node in injection_result.nodes]))

        cmd = [sys.executable, str(ctx.base_dir / "_internal" / "scripts" / "gemini_worker.py"), mission.worker, instruction]
        if final_context:
            cmd.extend(["-c"] + final_context)
        if output_path:
            cmd.extend(["-o", output_path])
        if mission.audit_requirements:
            cmd.extend(["-a", mission.audit_requirements])
        if model:
            cmd.extend(["--model", model])
        
        res = run_command(cmd, cwd=ctx.base_dir)
        success = res and res.returncode == 0
        if success:
            service.delete_mission(key)

        return CommandResult(
            success=success,
            message="Mission completed" if success else "Mission failed",
            exit_code=res.returncode if res else 1
        )

class JulesDispatcher(ICommand):
    @property
    def name(self) -> str:
        return "jules"

    @property
    def description(self) -> str:
        return "Dispatches a dynamic Jules mission."

    def execute(self, ctx: CommandContext) -> CommandResult:
        if not ctx.raw_args:
            interactive_script = ctx.base_dir / "_internal" / "scripts" / "run_jules_interactive.py"
            if interactive_script.exists():
                print("🚀 Entering Interactive Jules Command Center...")
                subprocess.run([sys.executable, str(interactive_script)], cwd=ctx.base_dir)
                return CommandResult(success=True, message="Interactive session closed.")

        key = ctx.raw_args[0]
        service = ctx.service_provider.get_jules_service()
        service.migrate_from_registry_dir()

        mission = service.get_mission(key)
        if not mission:
            msg = f"❌ Error: Key '{key}' not found in Jules registry."
            print(msg)
            return CommandResult(success=False, message=msg)

        if mission.type != MissionType.JULES:
            msg = f"❌ Error: Mission '{key}' is not a Jules mission."
            print(msg)
            return CommandResult(success=False, message=msg)

        command = mission.command or "create"
        cmd = [sys.executable, str(ctx.base_dir / "_internal" / "scripts" / "jules_bridge.py"), command]

        if command == "create":
            cmd.append(mission.title)
            if mission.file_path:
                cmd.extend(["-f", mission.file_path])
            else:
                cmd.append(mission.instruction_raw)
            cmd.extend(["--mission-key", key])
        elif command == "send-message":
            if not mission.session_id:
                return CommandResult(success=False, message="Error: session_id is required for send-message")
            cmd.append(mission.session_id)
            if mission.file_path:
                cmd.extend(["-f", mission.file_path])
            else:
                cmd.append(mission.instruction_raw)
            cmd.extend(["--mission-key", key])
        elif command in ["complete", "get-session", "status", "activities"]:
            if not mission.session_id:
                return CommandResult(success=False, message=f"Error: session_id is required for {command}")
            cmd.append(mission.session_id)
        
        if mission.wait:
            cmd.append("--wait")
        
        output_log = ctx.base_dir / "communications" / "jules_logs" / "last_run.md"
        output_log.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"🚀 Dispatching Jules Command: {command} (Mission: {key})...")
        
        try:
            with open(output_log, "w", encoding="utf-8") as f:
                result = subprocess.run(cmd, cwd=ctx.base_dir, capture_output=True, text=True)
                f.write(result.stdout)
                f.write(result.stderr)
                
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if "OK: Session created:" in line or "AGENT Jules Response:" in line or "Title:" in line:
                            print(f"   {line}")
                    print(f"✅ Success! Log: {output_log}")
                    service.delete_mission(key)
                    return CommandResult(success=True, message="Jules mission dispatched successfully.")
                else:
                    print(f"❌ Failed! (Exit Code: {result.returncode})")
                    return CommandResult(success=False, message="Jules mission failed.", exit_code=result.returncode)

        except Exception as e:
            return CommandResult(success=False, message=f"Error during Jules dispatch: {e}")
