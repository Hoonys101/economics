import sys
import subprocess
import datetime
import logging
from typing import List
from _internal.registry.api import ICommand, CommandContext, CommandResult
from _internal.scripts.core.commands import run_command
# from _internal.scripts.core.context_injector.service import ContextInjectorService
# from modules.tools.context_injector.api import InjectionRequestDTO

logger = logging.getLogger(__name__)

class GitReviewCommand(ICommand):
    @property
    def name(self) -> str:
        return "git-review"

    @property
    def description(self) -> str:
        return "Analyzes a branch for PR review and generates an AI report."

    def execute(self, ctx: CommandContext) -> CommandResult:
        args = ctx.raw_args
        base_dir = ctx.base_dir
        
        branch = args[0] if args else "main"
        instruction = args[1] if len(args) > 1 else "Analyze this PR."

        print(f"🔍 [Git-Review] Syncing and analyzing branch: {branch}")
        
        sync_cmd = [sys.executable, str(base_dir / "_internal" / "scripts" / "git_sync_checker.py"), branch]
        res = run_command(sync_cmd, cwd=base_dir, capture_output=True)
        if not res or not res.stdout.strip():
            return CommandResult(success=False, message="Failed to get latest commit.")
        
        commit_hash = res.stdout.strip().split('\n')[-1]
        print(f"📍 Target Commit: {commit_hash}")

        run_command(["git", "fetch", "origin", branch], cwd=base_dir)
        
        short_name = branch.split('/')[-1]
        diff_file = base_dir / "gemini-output" / "review" / f"pr_diff_{short_name}.txt"
        diff_file.parent.mkdir(parents=True, exist_ok=True)
        
        exclude_patterns = [":!*.txt", ":!*.csv", ":!*.log", ":!*.db"]
        cmd = ["git", "diff", f"origin/main...{commit_hash}", "--", "."] + exclude_patterns
        
        with open(diff_file, "w", encoding="utf-8") as f:
            subprocess.run(cmd, cwd=base_dir, stdout=f)

        diff_status_cmd = ["git", "diff", "--name-only", f"origin/main...{commit_hash}"]
        diff_status = subprocess.run(diff_status_cmd, cwd=base_dir, capture_output=True, text=True, encoding='utf-8')
        changed_files = diff_status.stdout.splitlines()
        
        # injector = ContextInjectorService()
        # injection_result = injector.analyze_context(InjectionRequestDTO(
        #     target_files=changed_files,
        #     include_tests=True,
        #     include_docs=True,
        #     max_dependency_depth=1
        # ))
        
        # final_context = [node.file_path for node in injection_result.nodes]
        # Only include files that exist in the local FS for standalone context.
        # New files are already covered by the diff file.
        final_context = [f for f in changed_files if (base_dir / f).is_file()]

        review_output = base_dir / "gemini-output" / "review" / f"pr_review_{short_name}.md"
        
        if review_output.exists():
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"pr_review_{short_name}_BACKUP_{timestamp}.md"
            backup_path = review_output.parent / backup_name
            print(f"🔄 Rotating old review to: {backup_name}")
            review_output.rename(backup_path)
            
        gemini_cmd = [
            sys.executable, 
            str(base_dir / "_internal" / "scripts" / "gemini_worker.py"), 
            "git-review", 
            instruction, 
            "-c", str(diff_file)
        ]
        if final_context:
            gemini_cmd.extend(final_context)
        
        print("🧠 Running AI Code Review...")
        with open(review_output, "w", encoding="utf-8") as f:
            # Note: We capture stderr to file, but if it fails, we should probably tell the user why.
            r = subprocess.run(gemini_cmd, cwd=base_dir, stdout=f, stderr=subprocess.PIPE, text=True)
            if r.stderr:
                f.write("\n--- STDERR ---\n")
                f.write(r.stderr)
        
        success = r.returncode == 0
        if success:
            print(f"✅ AI Review completed successfully.")
            print(f"📄 Report: {review_output}")
        else:
            print(f"❌ AI Review failed with exit code {r.returncode}")
            if r.stderr:
                print(f"⚠️ Error: {r.stderr.strip().splitlines()[-1]}")

        return CommandResult(
            success=success,
            message=f"Review complete. Report: {review_output}" if success else "AI Review failed",
            exit_code=r.returncode
        )

class MergeCommand(ICommand):
    @property
    def name(self) -> str:
        return "merge"

    @property
    def description(self) -> str:
        return "Executes a branch merge and cleanup sequence."

    def execute(self, ctx: CommandContext) -> CommandResult:
        branch = ctx.raw_args[0] if ctx.raw_args else ""
        if not branch:
            return CommandResult(success=False, message="Error: Branch name required for merge.")

        commands = [
            ["git", "checkout", "main"],
            ["git", "pull", "origin", "main"],
            ["git", "fetch", "origin", branch],
            ["git", "merge", f"origin/{branch}", "--no-edit"],
            ["git", "push", "origin", "main"],
            ["git", "push", "origin", "--delete", branch]
        ]

        for cmd in commands:
            res = subprocess.run(cmd, cwd=ctx.base_dir, capture_output=False)
            if res.returncode != 0 and "--delete" not in cmd:
                return CommandResult(
                    success=False, 
                    message=f"Stop: Merge sequence interrupted at '{' '.join(cmd)}'",
                    exit_code=res.returncode
                )
        
        return CommandResult(success=True, message=f"Branch {branch} successfully merged and cleaned up.")
