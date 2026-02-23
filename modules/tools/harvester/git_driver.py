import subprocess
import logging
from typing import List, Dict, Optional
from modules.tools.harvester.api import IGitDriver

logger = logging.getLogger(__name__)

class GitDriver(IGitDriver):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def _run_git(self, args: List[str], input_str: Optional[str] = None) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.base_dir,
                input=input_str,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            if result.returncode != 0:
                logger.debug(f"Git command failed: git {' '.join(args)} | Error: {result.stderr}")
                return None
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"Error running git command: {e}")
            return None

    def fetch_origin(self) -> None:
        self._run_git(["fetch", "origin", "--prune"])

    def list_remote_branches(self) -> List[str]:
        output = self._run_git(["branch", "-r"])
        if not output:
            return []
        return [b.strip() for b in output.split('\n') if "origin/" in b and "HEAD" not in b]

    def list_files_in_branch(self, branch: str) -> List[str]:
        # Use -z for null-terminated strings to handle spaces safely
        output = self._run_git(["ls-tree", "-r", "-z", "--name-only", branch])
        if not output:
            return []
        return [f for f in output.split('\0') if f]

    def get_commit_dates_batch(self, branch: str, file_paths: List[str]) -> Dict[str, int]:
        results = {}
        # Since K is small, individual calls are safe and provide accurate individual timestamps
        for path in file_paths:
            ts_str = self._run_git(["log", "-1", "--format=%ct", branch, "--", path])
            if ts_str and ts_str.isdigit():
                results[path] = int(ts_str)
            else:
                results[path] = 0
        return results

    def read_files_batch(self, branch: str, file_paths: List[str]) -> Dict[str, Optional[str]]:
        if not file_paths:
            return {}
        
        results: Dict[str, Optional[str]] = {}
        input_data = "\n".join([f"{branch}:{path}" for path in file_paths]) + "\n"
        
        # git cat-file --batch
        # Note: We need to handle the output stream carefully as it's mixed metadata and binary/text
        # For simplicity in this text-focused harvester, we use capture_output=True
        # but large files might need streaming.
        
        try:
            process = subprocess.Popen(
                ["git", "cat-file", "--batch"],
                cwd=self.base_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False # We handle encoding manually
            )
            stdout, stderr = process.communicate(input=input_data.encode('utf-8'))
            
            if process.returncode != 0:
                return {path: None for path in file_paths}

            results = {}
            offset = 0
            for path in file_paths:
                # Find metadata line (ends with \n)
                end_of_header = stdout.find(b'\n', offset)
                if end_of_header == -1:
                    break
                
                header = stdout[offset:end_of_header].decode('utf-8')
                offset = end_of_header + 1
                
                if "missing" in header:
                    results[path] = None
                    continue
                
                # Header format: <sha1> <type> <size>
                parts = header.split()
                if len(parts) < 3:
                    results[path] = None
                    continue
                
                size = int(parts[2])
                content_bytes = stdout[offset : offset + size]
                results[path] = content_bytes.decode('utf-8', errors='replace')
                
                # cat-file adds a newline after each object
                offset += size + 1
                
            return results
        except Exception as e:
            logger.error(f"Failed in read_files_batch: {e}")
            return {path: None for path in file_paths}

    def delete_remote_branch(self, branch: str) -> bool:
        clean_name = branch.replace("origin/", "")
        if clean_name in ["main", "master", "develop", "dev"]:
            return False
        res = self._run_git(["push", "origin", "--delete", clean_name])
        return res is not None
