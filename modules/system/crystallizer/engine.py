"""
Crystallizer Engine: Implementation of the Knowledge Recirculation Loop.
"""
import os
import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from modules.system.crystallizer.api import (
    ICrystallizerEngine, IInsightLoader, IManualSynthesizer,
    InsightEntry, InsightMetadata, ManualContext, ManualUpdateProposalDTO, ProposalDiff
)

class InsightLoader(IInsightLoader):
    def load_insights(self, insights_dir: str) -> List[InsightEntry]:
        entries = []
        path = Path(insights_dir)
        if not path.exists():
            return []

        for f in path.glob("*.md"):
            try:
                content = f.read_text(encoding="utf-8")
                # Parse frontmatter
                metadata = self._parse_frontmatter(content)
                if not metadata:
                    # Fallback or skip
                    continue
                
                # Strip frontmatter for content block
                content_block = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL).strip()
                
                entries.append(InsightEntry(
                    file_path=str(f),
                    metadata=metadata,
                    content_block=content_block
                ))
            except Exception as e:
                print(f"⚠️ Failed to parse insight {f.name}: {e}")
        return entries

    def _parse_frontmatter(self, content: str) -> Optional[InsightMetadata]:
        match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if match:
            try:
                data = yaml.safe_load(match.group(1))
                return InsightMetadata(
                    mission_key=data.get("mission_key", "unknown"),
                    date=str(data.get("date", datetime.now().strftime("%Y-%m-%d"))),
                    type=data.get("type", "General"),
                    target_manual=data.get("target_manual"),
                    actionable=data.get("actionable", False)
                )
            except yaml.YAMLError:
                return None
        return None

    def filter_actionable(self, insights: List[InsightEntry]) -> List[InsightEntry]:
        return [i for i in insights if i.metadata.get("actionable") and i.metadata.get("target_manual")]

class ManualSynthesizer(IManualSynthesizer):
    def synthesize_proposal(self, manual: ManualContext, insights: List[InsightEntry]) -> ManualUpdateProposalDTO:
        # Minimal viable implementation: Propose appending a "New Learnings" section
        # Real implementation would use LLM to merge text intelligently
        
        proposals = []
        
        combined_reasoning = "\n".join([f"- From {Path(i.file_path).name}" for i in insights])
        combined_content = "\n\n".join([f"### Insight from {i.metadata['date']}\n{i.content_block[:200]}..." for i in insights])
        
        diff = ProposalDiff(
            section_header="## New Learnings (Pending Integration)",
            original_text=None,
            proposed_text=combined_content,
            reasoning=f"Aggregated {len(insights)} actionable insights.\n{combined_reasoning}",
            source_insights=[i.file_path for i in insights]
        )
        proposals.append(diff)

        return ManualUpdateProposalDTO(
            target_manual=manual.file_path,
            generated_at=datetime.now().isoformat(),
            proposals=proposals,
            risk_assessment="Low: Appending new section only."
        )

class CrystallizerEngine(ICrystallizerEngine):
    def __init__(self):
        self.loader = InsightLoader()
        self.synthesizer = ManualSynthesizer()

    def run_crystallization(self, insights_dir: str, manuals_dir: str, dry_run: bool = True) -> List[ManualUpdateProposalDTO]:
        insights = self.loader.load_insights(insights_dir)
        actionable = self.loader.filter_actionable(insights)
        
        grouped = {}
        for entry in actionable:
            target = entry.metadata["target_manual"]
            if target not in grouped:
                grouped[target] = []
            grouped[target].append(entry)

        results = []
        for target_manual, group in grouped.items():
            manual_path = Path(manuals_dir) / Path(target_manual).name
            if not manual_path.exists():
                print(f"⚠️ Target manual not found: {manual_path}")
                continue

            manual_ctx = ManualContext(
                file_path=str(manual_path),
                current_content=manual_path.read_text(encoding="utf-8"),
                last_updated=datetime.fromtimestamp(manual_path.stat().st_mtime)
            )

            proposal = self.synthesizer.synthesize_proposal(manual_ctx, group)
            results.append(proposal)
            
            # Output the proposal to a file
            output_name = f"PROPOSAL_{Path(target_manual).stem}_{datetime.now().strftime('%Y%m%d')}.md"
            output_path = Path("design/3_work_artifacts/drafts") / output_name
            self._write_proposal(proposal, output_path)
            
        return results

    def _write_proposal(self, dto: ManualUpdateProposalDTO, path: Path):
        content = f"# Manual Update Proposal: {dto['target_manual']}\n"
        content += f"> Generated: {dto['generated_at']}\n\n"
        
        for p in dto['proposals']:
            content += f"## Proposed Change: {p.section_header}\n"
            content += f"**Reasoning**:\n{p.reasoning}\n\n"
            content += "### Diff\n"
            if p.original_text:
                content += "```diff\n- OLD\n" + p.original_text + "\n```\n"
            content += "```diff\n+ NEW\n" + p.proposed_text + "\n```\n\n"
            
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"✅ Generated Proposal: {path}")

if __name__ == "__main__":
    # Quick CLI for testing
    import sys
    engine = CrystallizerEngine()
    engine.run_crystallization("communications/insights", "_internal/manuals")
