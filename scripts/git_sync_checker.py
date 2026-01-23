import sys
import subprocess
import re
import os


def run_command(command, cwd=None):
    """Run a shell command and return stdout. Raises error on failure."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(command)}\nstderr: {e.stderr}")
        raise


def sync_and_find_commit(identifier):
    """
    Syncs with remote and finds the latest commit hash for a given session ID or branch name.
    """
    sys.stderr.write(f"🔄 Syncing Git to find latest commit for: {identifier}...\n")

    # 1. Force Fetch All
    try:
        run_command(["git", "fetch", "--all"])
        sys.stderr.write("   ✅ Git fetch --all completed.\n")
    except Exception as e:
        sys.stderr.write(f"   ⚠️ Git fetch failed: {e}\n")
        return None

    # Determine if identifier is a session ID (digits) or branch name
    target_branch = None
    if re.match(r"^\d+$", identifier):
        # Session ID: Find remote branch containing this ID
        sys.stderr.write(
            f"   🔎 Searching for remote branches containing session ID: {identifier}\n"
        )
        try:
            # List all remote branches
            remote_branches_output = run_command(["git", "branch", "-r"])
            branches = [b.strip() for b in remote_branches_output.splitlines()]

            # Filter for branches containing the session ID
            matches = [b for b in branches if identifier in b]

            if not matches:
                sys.stderr.write("   ❌ No remote branch found for this session ID.\n")
                return None

            target_branch = matches[0].replace("origin/", "")
            sys.stderr.write(f"   ✅ Found target branch: {target_branch}\n")

        except Exception as e:
            sys.stderr.write(f"   ❌ Error finding branch: {e}\n")
            return None
    else:
        # Assumed to be a branch name
        target_branch = identifier

    # 2. Check ls-remote for the TRUE latest commit on the server
    sys.stderr.write(f"   📡 Checking ls-remote for branch: {target_branch}\n")
    try:
        output = run_command(["git", "ls-remote", "origin", target_branch])
        if not output:
            sys.stderr.write(
                "   ❌ ls-remote returned no result. Branch might not exist on remote.\n"
            )
            return None

        parts = output.split()
        if parts:
            latest_commit_hash = parts[0]
            sys.stderr.write(f"   🎯 Latest Remote Commit: {latest_commit_hash}\n")
            return latest_commit_hash
        else:
            sys.stderr.write("   ❌ Could not parse ls-remote output.\n")
            return None

    except Exception as e:
        sys.stderr.write(f"   ❌ ls-remote failed: {e}\n")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write(
            "Usage: python git_sync_checker.py <session_id_or_branch_name>\n"
        )
        sys.exit(1)

    identifier = sys.argv[1]
    last_commit = sync_and_find_commit(identifier)

    if last_commit:
        # STDOUT ONLY contains the hash
        print(last_commit)
        sys.exit(0)
    else:
        sys.exit(1)
