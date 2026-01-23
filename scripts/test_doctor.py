import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
WORKER_SCRIPT = BASE_DIR / "scripts" / "gemini_worker.py"


def run_worker(worker_type, instruction, context_files=None):
    cmd = ["python", str(WORKER_SCRIPT), worker_type, instruction]
    if context_files:
        cmd.extend(["--context"] + context_files)

    # We want to capture the output of the worker to print it nicely
    result = subprocess.run(cmd, text=True, capture_output=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"❌ Worker failed: {result.stderr}")
        return None
    return result.stdout


def main():
    print("🩺 Test Doctor: Initializing...")

    # 1. Run Pytest
    print("🧪 Running Pytest (this may take a moment)...")
    # Run with -v for details, but we'll capture it
    result = subprocess.run(
        ["pytest"], cwd=BASE_DIR, capture_output=True, text=True, encoding="utf-8"
    )

    if result.returncode == 0:
        print("\n✅ All Tests Passed! System is healthy.")
        print(result.stdout[-500:])  # Print last bit of success message
        sys.exit(0)

    # 2. Analyze Failure
    print("\n⚠️ Tests Failed. Analyzing logs...")
    log_content = result.stdout + result.stderr

    # Save log to temp file to use as context (too big for CLI arg usually)
    log_file = BASE_DIR / "reports" / "temp" / "pytest_failure.log"
    log_file.parent.mkdir(exist_ok=True, parents=True)
    log_file.write_text(log_content, encoding="utf-8")

    instruction = (
        "Analyze the attached pytest log. Identify the failing tests and the ROOT CAUSE. "
        "Summarize the findings in exactly 3 lines: "
        "1. Failing Module/Test "
        "2. Error Message/Type "
        "3. Suggested Fix or Root Cause"
    )

    summary = run_worker(
        "reporter", instruction, context_files=[f"reports/temp/pytest_failure.log"]
    )

    print("\n🩺 Diagnosis Report:")
    print("=" * 60)
    if summary:
        print(summary)
    else:
        print("Failed to generate summary.")
    print("=" * 60)
    print(f"\n📄 Full Log: {log_file}")
    sys.exit(1)


if __name__ == "__main__":
    main()
