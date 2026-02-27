
import os
import subprocess
import sys
import time

def check_batch(files):
    print(f"Checking batch: {len(files)} files", flush=True)
    try:
        start = time.time()
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only"] + files,
            capture_output=True,
            text=True,
            timeout=60
        )
        elapsed = time.time() - start
        if result.returncode == 0:
            print(f"  OK ({elapsed:.2f}s)", flush=True)
            return True, None
        else:
            print(f"  FAILED ({elapsed:.2f}s)", flush=True)
            # print(result.stderr, flush=True)
            return False, "Failed"
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT", flush=True)
        return False, "Timeout"

test_files = []
for root, dirs, files in os.walk("tests/unit"):
    for f in files:
        if f.startswith("test_") and f.endswith(".py"):
            test_files.append(os.path.join(root, f))

test_files.sort()

batch_size = 20
for i in range(0, len(test_files), batch_size):
    batch = test_files[i:i+batch_size]
    print(f"Batch {i//batch_size + 1}: {batch[0]} ... {batch[-1]}", flush=True)
    success, error = check_batch(batch)
    if not success:
        print(f"!!! Error in batch {i//batch_size + 1}", flush=True)
        for f in batch:
            print(f"Checking individually: {f}", flush=True)
            s, e = check_batch([f])
            if not s:
                 print(f"FOUND POISON FILE: {f}", flush=True)
                 break
        break
print("Finished diagnosis.", flush=True)
