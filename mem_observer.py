import gc
import sys
import logging
from collections import Counter
from unittest.mock import MagicMock

logger = logging.getLogger(__name__)

class MemoryLeakObserver:
    """
    Observer to monitor object growth and potential memory leaks across test executions.
    """
    def __init__(self):
        self.snapshots = {}

    def take_snapshot(self, stage_name: str):
        gc.collect()
        counts = Counter()
        for obj in gc.get_objects():
            counts[type(obj).__name__] += 1
        self.snapshots[stage_name] = counts
        logger.info(f"MEMORY_SNAPSHOT | Stage: {stage_name} | Total Objects: {sum(counts.values())}")

    def report_delta(self, start_stage: str, end_stage: str):
        if start_stage not in self.snapshots or end_stage not in self.snapshots:
            logger.warning(f"MEMORY_REPORT | Missing snapshot for {start_stage} or {end_stage}")
            return

        start_counts = self.snapshots[start_stage]
        end_counts = self.snapshots[end_stage]
        
        delta = end_counts - start_counts
        if not delta:
            logger.info(f"MEMORY_REPORT | No growth detected between {start_stage} and {end_stage}")
            return

        growth = sorted([(k, v) for k, v in delta.items() if v > 0], key=lambda x: x[1], reverse=True)
        
        if growth:
            logger.info(f"--- MEMORY GROWTH REPORT: {start_stage} -> {end_stage} ---")
            for cls_name, count in growth[:10]:
                logger.info(f"  {cls_name}: +{count}")
            
            # Specific check for Mocks
            mock_growth = delta.get('MagicMock', 0)
            if mock_growth > 0:
                logger.warning(f"CRITICAL | MagicMock growth detected: +{mock_growth}")
        else:
            logger.info(f"MEMORY_REPORT | No net object growth between {start_stage} and {end_stage}")

# Global observer instance
observer = MemoryLeakObserver()
