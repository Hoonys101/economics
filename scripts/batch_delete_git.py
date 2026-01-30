
import subprocess

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode().strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output.decode()}"

with open('remotes.txt', 'r') as f:
    branches = [line.strip() for line in f if line.strip()]

to_delete = []
for b in branches:
    if b in ['origin', 'origin/main', 'origin/HEAD', 'main']:
        continue
    if b.startswith('origin/'):
        to_delete.append(b.replace('origin/', '', 1))

print(f"Total branches to delete: {len(to_delete)}")

batch_size = 10
for i in range(0, len(to_delete), batch_size):
    batch = to_delete[i:i + batch_size]
    print(f"Deleting batch {i//batch_size + 1}: {batch}")
    cmd = f"git push origin --delete {' '.join(batch)}"
    print(run(cmd))

print("\n--- Final sync ---")
print(run("git remote prune origin"))
print(run("git fetch -p"))
print("\n--- Remaining ---")
print(run("git branch -a"))
