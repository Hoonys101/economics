import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from modules.tools.harvester.api import (
    IHarvesterService, IScoringEngine, IGitDriver, 
    HarvestConfigDTO, HarvestResultDTO, HarvestCandidateDTO
)

logger = logging.getLogger(__name__)

class ScoringEngine(IScoringEngine):
    def calculate_static_score(self, file_path: str) -> int:
        score = 0
        name_lower = os.path.basename(file_path).lower()
        path_lower = file_path.lower()
        
        # Priority Keywords
        if any(keyword in name_lower for keyword in ["audit", "report", "finding", "crystallization", "handover"]):
            score += 100
            
        # Path Relevance
        if any(p in path_lower for p in ["design/drafts/audits/", "artifacts/reports/", "communications/reports/"]):
            score += 50
            
        # Noise Keywords
        if any(keyword in name_lower for keyword in ["ledger", "archived", "status"]):
            score -= 50
            
        return score

class HarvesterService(IHarvesterService):
    def __init__(self, git_driver: IGitDriver, scoring_engine: IScoringEngine):
        self.git = git_driver
        self.scorer = scoring_engine

    def execute_harvest(self, config: HarvestConfigDTO) -> HarvestResultDTO:
        logger.info(f"🌾 [Harvester] Starting Optimized Harvest (Max Branches: {config['max_branches']})")
        
        harvested_files = []
        errors = []
        total_score = 0

        # Create harvest directory
        harvest_dir = Path(config["harvest_dir"])
        harvest_dir.mkdir(parents=True, exist_ok=True)

        # 1. Fetch & Discovery
        self.git.fetch_origin()
        branches = self.git.list_remote_branches()
        
        if not branches:
            return HarvestResultDTO(True, [], [], 0)

        # Matched branches by pattern
        target_patterns = config.get("target_patterns", [])
        matched_branches = []
        if target_patterns:
            matched_branches = [b for b in branches if any(p in b for p in target_patterns)]
        else:
            # Fallback to all non-protected branches
            protected = ["origin/main", "origin/master", "origin/develop", "origin/dev"]
            matched_branches = [b for b in branches if b not in protected]

        if not matched_branches:
            return HarvestResultDTO(True, [], [], 0)

        # Sort branches by date (O(B) processes where B is number of matched branches)
        # This is acceptable as B is usually small.
        branch_dates = self.git.get_commit_dates_batch("HEAD", matched_branches) # Using current HEAD for comparison or just individual logs
        # Correction: GitDriver.get_commit_dates_batch takes a list of files in a branch.
        # For branch dates, we need individual calls or a different helper.
        # Let's add a list_branch_dates to GitDriver or just do it here.
        
        sorted_branches = []
        for b in matched_branches:
            # Reusing get_commit_dates_batch for just the branch head
            ts_map = self.git.get_commit_dates_batch(b, ["."]) # "." refers to the branch head
            sorted_branches.append((b, ts_map.get(".", 0)))
        
        sorted_branches.sort(key=lambda x: x[1], reverse=True)
        top_branches = sorted_branches[:config["max_branches"]]

        for branch_name, branch_ts in top_branches:
            try:
                files, branch_score = self._process_branch(branch_name, config, harvest_dir)
                harvested_files.extend(files)
                total_score += branch_score
            except Exception as e:
                msg = f"Failed to process branch {branch_name}: {e}"
                logger.error(msg)
                errors.append(msg)

        return HarvestResultDTO(True, harvested_files, errors, total_score)

    def _process_branch(self, branch: str, config: HarvestConfigDTO, harvest_dir: Path) -> tuple[List[str], int]:
        logger.info(f"📂 Scanning Branch: {branch}")
        
        # 1. Discovery (ls-tree) - O(1)
        all_files = self.git.list_files_in_branch(branch)
        
        # 2. Static Scoring (In-Memory)
        candidates = []
        target_dirs = ["design/", "artifacts/reports/", "communications/reports/", "reports/"]
        
        for f in all_files:
            if not f.endswith(".md"):
                continue
            if not any(td in f for td in target_dirs):
                continue
                
            score = self.scorer.calculate_static_score(f)
            candidates.append(HarvestCandidateDTO(path=f, branch=branch, score=score))

        if not candidates:
            return [], 0

        # 3. Pruning: Sort by static score and pick Top K
        # K = max_files * 2 provides enough buffer for date tie-breaking without log spam
        k = config["max_files_per_branch"] * 5 
        candidates.sort(key=lambda x: x.score, reverse=True)
        top_k = candidates[:k]

        # 4. Batch Date Fetch for Top K - O(K)
        paths = [c.path for c in top_k]
        dates = self.git.get_commit_dates_batch(branch, paths)

        # 5. Enrich & Final Sort
        final_candidates = []
        for c in top_k:
            ts = dates.get(c.path, 0)
            # Re-create DTO with timestamp
            final_candidates.append(HarvestCandidateDTO(
                path=c.path, branch=c.branch, score=c.score, timestamp=ts
            ))
        
        final_candidates.sort(key=lambda x: (x.score, x.timestamp), reverse=True)
        winners = final_candidates[:config["max_files_per_branch"]]

        # 6. Batch Content Download - O(1) subprocess
        winner_paths = [w.path for w in winners]
        contents = self.git.read_files_batch(branch, winner_paths)

        stored_files = []
        branch_score = 0

        # 7. Save to disk
        for winner in winners:
            content = contents.get(winner.path)
            if not content:
                continue

            safe_branch = branch.replace("origin/", "").replace("/", "-")
            f_name = Path(winner.path).name
            filename = f"{safe_branch}__{f_name}"
            save_path = harvest_dir / filename
            
            f_date_str = datetime.fromtimestamp(winner.timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            with open(save_path, "w", encoding="utf-8") as out_file:
                header = (
                    f"--- SOURCE INFO ---\n"
                    f"Branch: {branch}\n"
                    f"Score: {winner.score}\n"
                    f"File Date: {f_date_str}\n"
                    f"Harvested: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"---\n\n"
                )
                out_file.write(header + content)
            
            logger.info(f"      💾 Harvested (Score {winner.score}): {filename}")
            stored_files.append(filename)
            branch_score += winner.score

        # 8. Cleanup
        if config["cleanup_remote"]:
            self.git.delete_remote_branch(branch)

        return stored_files, branch_score
