
import subprocess

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode().strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output.decode()}"

# 1. Delete all local branches except main
print("--- Cleaning Local Branches ---")
local_branches = run("git branch --format='%(refname:short)'").split('\n')
for branch in local_branches:
    branch = branch.strip()
    if branch and branch != 'main':
        print(f"Deleting local branch: {branch}")
        print(run(f"git branch -D {branch}"))

# 2. Delete remote merged branches
print("\n--- Cleaning Remote Merged Branches ---")
remote_merged = run("git branch -r --merged origin/main").split('\n')
for rb in remote_merged:
    rb = rb.strip()
    if not rb or 'origin/main' in rb or 'origin/HEAD' in rb:
        continue
    
    # Extract branch name from origin/branch_name
    branch_name = rb.replace('origin/', '', 1)
    if branch_name:
        print(f"Deleting remote branch: {branch_name}")
        print(run(f"git push origin --delete {branch_name}"))

# 3. Final Prune
print("\n--- Final Prune ---")
print(run("git remote prune origin"))
print(run("git fetch --prune"))

print("\n--- Current Status ---")
print(run("git branch -a"))
