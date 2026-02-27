
import os
import subprocess
import sys

def check_collection(path):
    print(f"Checking: {path}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", path],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"  OK: {path}")
            return True
        else:
            print(f"  FAIL: {path}")
            print(result.stdout)
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"  HANG: {path}")
        return False

def discover_files(root):
    test_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            if filename.startswith("test_") and filename.endswith(".py"):
                test_files.append(os.path.join(dirpath, filename))
    return sorted(test_files)

if __name__ == "__main__":
    root = "tests/unit"
    files = discover_files(root)
    print(f"Found {len(files)} test files.")
    
    for f in files:
        if not check_collection(f):
            print(f"\nPotential culprit identified: {f}")
            # break # Keep going to see if there are others
