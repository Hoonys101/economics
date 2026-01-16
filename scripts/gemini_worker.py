
import subprocess
import sys
import os
from pathlib import Path
import shutil
import argparse
from abc import ABC, abstractmethod

# Configuration
BASE_DIR = Path(__file__).parent.parent
MANUALS_DIR = BASE_DIR / "design" / "manuals"

class BaseGeminiWorker(ABC):
    """
    Abstract base class for Gemini Workers.
    Handles the interaction with gemini-cli using a specific manual.
    """
    def __init__(self, manual_filename: str):
        self.manual_path = MANUALS_DIR / manual_filename
        if not self.manual_path.exists():
            raise FileNotFoundError(f"❌ Manual not found: {self.manual_path}")
        
        if not shutil.which("gemini"):
            raise EnvironmentError("❌ 'gemini' command not found in PATH.")

    def get_system_prompt(self) -> str:
        try:
            with open(self.manual_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"❌ Error reading manual: {e}")

    def run_gemini(self, instruction: str, context_files: list[str] = None, manual_override: Path = None) -> str:
        """
        Executes gemini-cli with the system prompt, context files, and instruction.
        If manual_override is provided, use that manual instead of self.manual_path.
        """
        # Use override manual if provided, otherwise use default
        manual_to_use = manual_override if manual_override else self.manual_path
        try:
            with open(manual_to_use, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except Exception as e:
            raise RuntimeError(f"❌ Error reading manual {manual_to_use}: {e}")
        
        # Build Context Block
        context_block = ""
        if context_files:
            context_block += "\n\n[Context Files]\n"
            expanded_files = []
            for item in context_files:
                path = BASE_DIR / item
                if path.is_dir():
                    # If it's a directory, add all .py files within it
                    for py_file in path.glob("**/*.py"):
                        expanded_files.append(py_file.relative_to(BASE_DIR))
                else:
                    expanded_files.append(Path(item))

            for rel_path in expanded_files:
                abs_path = BASE_DIR / rel_path
                if abs_path.exists() and abs_path.is_file():
                    try:
                        content = abs_path.read_text(encoding='utf-8')
                        context_block += f"\nFile: {rel_path}\n```\n{content}\n```\n"
                        print(f"📖 Attached context: {rel_path}")
                    except Exception as e:
                        print(f"⚠️ Failed to read context file {rel_path}: {e}")
                else:
                    print(f"⚠️ Context file not found or is not a file: {rel_path}")

        full_input = f"{system_prompt}{context_block}\n\n---\n\n{instruction}"

        print(f"🚀 [GeminiWorker] Running task with manual: {manual_to_use.name}")
        
        try:
            process = subprocess.run(
                ["gemini"], 
                input=full_input, 
                text=True, 
                capture_output=True, 
                encoding='utf-8',
                shell=True 
            )
            
            if process.returncode != 0:
                raise RuntimeError(f"Gemini CLI Error (Code {process.returncode}):\n{process.stderr}")
            
            return process.stdout

        except Exception as e:
            raise RuntimeError(f"Error executing gemini subprocess: {e}")

    @abstractmethod
    def execute(self, instruction: str, context_files: list[str] = None, **kwargs):
        """
        Specific execution logic for the worker.
        """
        pass

class SpecDrafter(BaseGeminiWorker):
    """
    Worker for drafting specifications.
    Saves output to design/drafts/
    """
    def __init__(self):
        super().__init__("spec_writer.md")

    def execute(self, instruction: str, context_files: list[str] = None, audit_file: str = None, **kwargs):
        # 1. Internal Pre-flight Audit (Auto-Encapsulated)
        audit_context = ""
        if context_files:
            print(f"🔍 [Auto-Audit] Analyzing context files for architectural risks...")
            audit_instruction = (
                f"Perform a strict Pre-flight Audit on the provided context files based on the task: '{instruction}'.\n"
                "Identify:\n"
                "1. Hidden dependencies or God Classes.\n"
                "2. Potential circular imports.\n"
                "3. Violations of Single Responsibility Principle (SRP).\n"
                "4. Risks to existing tests.\n"
                "Output ONLY the critical risks and architectural constraints that must be respected in the Spec."
            )
            try:
                # Use reporter.md manual for audit pass (different from spec_writer.md)
                audit_result = self.run_gemini(audit_instruction, context_files, manual_override=MANUALS_DIR / "reporter.md")
                audit_context = (
                    "\n\n" + "="*40 + "\n"
                    "🔍 [AUTO-AUDIT FINDINGS]\n"
                    "The following architectural risks were identified during the internal pre-flight check.\n"
                    "You MUST address these items in the Specification:\n\n"
                    + audit_result + "\n"
                    + "="*40 + "\n\n"
                )
                print("✅ Auto-Audit Complete. Findings integrated into Spec Context.")
            except Exception as e:
                print(f"⚠️ Auto-Audit failed (skipping): {e}")

        # 2. External Audit File Injection (Optional Override)
        if audit_file:
            audit_path = BASE_DIR / audit_file
            if audit_path.exists():
                print(f"🚨 Injecting External Audit Findings from: {audit_path.name}")
                audit_content = audit_path.read_text(encoding='utf-8')
                # Append external audit to internal audit context
                audit_context += (
                    "\n\n" + "="*40 + "\n"
                    "🚨 [EXTERNAL AUDIT REPORT]\n"
                    + audit_content + "\n"
                    + "="*40 + "\n\n"
                )

        # 3. Main Spec Drafting
        full_instruction = audit_context + instruction
        
        print(f"📄 Drafting Spec with instruction: '{instruction[:60]}...'")
        result = self.run_gemini(full_instruction, context_files)
        
        # Save to draft file
        output_dir = BASE_DIR / "design" / "drafts"
        output_dir.mkdir(exist_ok=True, parents=True)
        
        safe_name = "".join([c if c.isalnum() else "_" for c in instruction[:30] if c.isalnum() or c == ' ']).strip().replace(" ", "_")[:30]
        from datetime import datetime
        timestamp = datetime.now().strftime("%H%M%S") 
        output_file = output_dir / f"draft_{timestamp}_{safe_name}.md"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result)
            
        print(f"\n✅ Spec Draft Saved: {output_file}")
        print("="*60)
        print(result[:1000] + "\n..." if len(result) > 1000 else result)
        print("="*60)

class GitReviewer(BaseGeminiWorker):
    """
    Worker for analyzing git diffs and generating code review reports.
    """
    def __init__(self):
        super().__init__("git_reviewer.md")

    def execute(self, instruction: str, context_files: list[str] = None, **kwargs):
        print(f"🕵️  Reviewing Code with instruction: '{instruction}'...")
        result = self.run_gemini(instruction, context_files)

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join([c if c.isalnum() else "_" for c in instruction[:20]]).strip("_")
        
        output_dir = BASE_DIR / "design" / "gemini_output" 
        output_dir.mkdir(exist_ok=True, parents=True)
        
        print("\n📝 [Review Report]")
        print("="*60)
        print(result)
        print("="*60)
        
        output_file = output_dir / f"review_backup_{timestamp}_{safe_name}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result)
            
class Reporter(BaseGeminiWorker):
    """
    Worker for analyzing code and generating reports.
    Saves output to reports/temp/
    """
    def __init__(self):
        super().__init__("reporter.md")

    def execute(self, instruction: str, context_files: list[str] = None, **kwargs):
        print(f"🕵️  Generating Report for: '{instruction}'...")
        result = self.run_gemini(instruction, context_files)

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join([c if c.isalnum() else "_" for c in instruction[:20]]).strip("_")
        
        output_dir = BASE_DIR / "reports" / "temp"
        output_dir.mkdir(exist_ok=True, parents=True)
        output_file = output_dir / f"report_{timestamp}_{safe_name}.md"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result)
            
        print(f"\n✅ Report Saved: {output_file}")
        print("="*60)
        print(result[:500] + "\n..." if len(result) > 500 else result)
        print("="*60)

class GitOperator(BaseGeminiWorker):
    """
    Worker for generating Git commands.
    Can auto-execute commands if requested.
    """
    def __init__(self):
        super().__init__("git_operator.md")

    def execute(self, instruction: str, context_files: list[str] = None, auto_run: bool = False, **kwargs):
        print(f"🐙 analyzing Git operation: '{instruction}'...")
        
        # Enhance instruction with current git status if possible
        try:
            status_proc = subprocess.run(["git", "status"], cwd=BASE_DIR, capture_output=True, text=True, encoding='utf-8')
            git_status = status_proc.stdout
            instruction += f"\n\n[Current Git Status]\n{git_status}"
        except Exception as e:
            print(f"⚠️ Could not fetch git status: {e}")

        result = self.run_gemini(instruction, context_files)
        
        # Parse JSON
        import json
        import re
        
        try:
            # Extract JSON block if surrounded by markdown code fences
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = result

            plan = json.loads(json_str)
            
            print("\n🤖 [GitPlan]")
            print(f"Reasoning: {plan.get('reasoning', 'No reasoning provided')}")
            print(f"Risk Level: {plan.get('risk_level', 'UNKNOWN')}")
            print("Commands:")
            for cmd in plan.get('commands', []):
                print(f"  $ {cmd}")
                
            if auto_run:
                if plan.get('risk_level') == 'HIGH':
                    print("\n⚠️ HIGH RISK DETECTED. Stopping auto-run for safety.")
                    return

                print("\n🚀 Auto-Running Commands...")
                for cmd in plan.get('commands', []):
                    print(f"Executing: {cmd}")
                    # Use string command for shell=True, ensure quotes are handled by shell
                    proc = subprocess.run(cmd, shell=True, cwd=BASE_DIR)
                    if proc.returncode != 0:
                        print(f"❌ Command failed: {cmd}")
                        break
                print("✅ Git Operation Completed.")

        except json.JSONDecodeError:
            print(f"❌ Failed to parse JSON response from Gemini CLI:\n{result}")
        except Exception as e:
            print(f"❌ Error during execution: {e}")

class ContextManager(BaseGeminiWorker):
    """
    Worker for summarizing state and creating snapshots.
    """
    def __init__(self):
        super().__init__("context_manager.md")

    def execute(self, instruction: str, context_files: list[str] = None, output_file: str = None, **kwargs):
        print(f"🧠 Distilling Context: '{instruction}'...")
        result = self.run_gemini(instruction, context_files)
        
        target_file = Path(output_file) if output_file else BASE_DIR / "design" / "snapshots" / "latest_snapshot.md"
        target_file.parent.mkdir(exist_ok=True, parents=True)
        
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(result)
            
        print(f"\n✅ Content Updated: {target_file}")
        print("="*60)
        print(result[:500] + "..." if len(result) > 500 else result)
        print("="*60)

class Validator(BaseGeminiWorker):
    """
    Worker for validating code against architecture rules.
    """
    def __init__(self):
        super().__init__("validator.md")

    def execute(self, instruction: str, context_files: list[str] = None, **kwargs):
        print(f"⚖️ Validating Protocol: '{instruction}'...")
        result = self.run_gemini(instruction, context_files)
        
        print("\n⚖️ [Validation Results]")
        print("="*60)
        print(result)
        print("="*60)

def main():
    parser = argparse.ArgumentParser(description="Gemini Worker Interface")
    subparsers = parser.add_subparsers(dest="worker_type", help="Type of worker to run")
    subparsers.required = True

    # Spec Drafter
    spec_parser = subparsers.add_parser("spec", help="Draft a new specification")
    spec_parser.add_argument("instruction", help="Instruction for the spec writer")
    spec_parser.add_argument("--context", "-c", nargs="+", help="List of files to read as context")
    spec_parser.add_argument("--audit", "-a", help="Path to Pre-flight Audit report to inject as context")

    # Git Operator
    git_parser = subparsers.add_parser("git", help="Generate git commands")
    git_parser.add_argument("instruction", help="Instruction for the git operator")
    git_parser.add_argument("--context", "-c", nargs="+", help="List of files to read as context")
    git_parser.add_argument("--auto-run", action="store_true", help="Automatically execute the generated commands")

    # Reporter
    reporter_parser = subparsers.add_parser("reporter", help="Analyze and Report")
    reporter_parser.add_argument("instruction", help="Instruction for the reporter")
    reporter_parser.add_argument("--context", "-c", nargs="+", help="List of files to read as context")

    # Context Manager / Scribe
    context_parser = subparsers.add_parser("context", help="Manage session context and snapshots")
    context_parser.add_argument("instruction", help="Instruction for the context manager")
    context_parser.add_argument("--context", "-c", nargs="+", help="List of files to read as context")
    context_parser.add_argument("--output", "-o", help="Specific output file path (optional)")

    # Validator
    validator_parser = subparsers.add_parser("verify", help="Validate protocol and architecture")
    validator_parser.add_argument("instruction", help="Instruction for the validator")
    validator_parser.add_argument("--context", "-c", nargs="+", help="List of files to read as context")

    # Auditor (Uses Reporter logic)
    auditor_parser = subparsers.add_parser("audit", help="Identify technical debt and patterns")
    auditor_parser.add_argument("instruction", help="Instruction for the auditor")
    auditor_parser.add_argument("--context", "-c", nargs="+", help="List of files to read as context")

    # Git Reviewer
    reviewer_parser = subparsers.add_parser("git-review", help="Analyze git diffs and report issues")
    reviewer_parser.add_argument("instruction", help="Instruction for the reviewer")
    reviewer_parser.add_argument("--context", "-c", nargs="+", help="List of files to read as context")

    args = parser.parse_args()

    try:
        worker_map = {
            "spec": SpecDrafter,
            "git": GitOperator,
            "reporter": Reporter,
            "context": ContextManager,
            "verify": Validator,
            "audit": Reporter,
            "git-review": GitReviewer
        }
        
        if args.worker_type in worker_map:
            worker = worker_map[args.worker_type]()
            worker.execute(
                args.instruction, 
                context_files=getattr(args, 'context', None),
                auto_run=getattr(args, 'auto_run', False),
                output_file=getattr(args, 'output', None),
                audit_file=getattr(args, 'audit', None)
            )
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
