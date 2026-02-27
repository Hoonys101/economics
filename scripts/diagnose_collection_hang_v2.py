
import os
import subprocess
import sys
import time

def check_collection(path):
    # print(f"Checking: {path}") # Silenced for cleaner output
    try:
        start = time.time()
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-c", "pytest.ini", path],
            capture_output=True,
            text=True,
            timeout=15
        )
        duration = time.time() - start
        if result.returncode == 0:
            return True, duration, ""
        else:
            return False, duration, result.stderr + result.stdout
    except subprocess.TimeoutExpired:
        return None, 15, "TIMEOUT"

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
    print(f"Found {len(files)} test files in {root}.")
    
    for i, f in enumerate(files):
        print(f"[{i+1}/{len(files)}] {f} ...", end=" ", flush=True)
        status, duration, error = check_collection(f)
        if status is True:
            print(f"OK ({duration:.2f}s)")
        elif status is False:
            print(f"FAIL ({duration:.2f}s)")
            # print(error)
        else:
            print(f"HANG (TIMEOUT)")
            print(f"\nPotential culprit: {f}")
            # break
