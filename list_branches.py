
import subprocess

def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode().strip()

print("--- LOCAL BRANCHES ---")
branches = run("git branch -vv").split('\n')
for b in branches:
    print(b)

print("\n--- MERGED INTO MAIN ---")
merged = run("git branch --merged main").split('\n')
for b in merged:
    print(b)

print("\n--- REMOTE MERGED INTO MAIN ---")
try:
    remote_merged = run("git branch -r --merged origin/main").split('\n')
    for b in remote_merged:
        print(b)
except:
    print("Error checking remote merged")
