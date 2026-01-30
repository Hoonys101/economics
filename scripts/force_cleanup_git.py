
import subprocess

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode().strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output.decode()}"

print("--- FORCED CLEANUP: DELETING ALL BUT MAIN ---")

# 1. Local
local_branches = run("git branch --format='%(refname:short)'").split('\n')
for b in local_branches:
    b = b.strip()
    if b and b != 'main':
        print(f"Force deleting local: {b}")
        print(run(f"git branch -D {b}"))

# 2. Remote
remote_branches = run("git branch -r --format='%(refname:short)'").split('\n')
for rb in remote_branches:
    rb = rb.strip()
    if not rb or 'origin/main' in rb or 'origin/HEAD' in rb:
        continue
    
    branch_name = rb.replace('origin/', '', 1)
    if branch_name:
        print(f"Force deleting remote: {branch_name}")
        print(run(f"git push origin --delete {branch_name}"))

print("\n--- Final sync ---")
print(run("git remote prune origin"))
print(run("git fetch -p"))
print("\n--- Remaining ---")
print(run("git branch -a"))
