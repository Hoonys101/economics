from _typeshed import Incomplete
from unittest.mock import MagicMock as MagicMock

logger: Incomplete

class MemoryLeakObserver:
    """
    Observer to monitor object growth and potential memory leaks across test executions.
    """
    snapshots: Incomplete
    def __init__(self) -> None: ...
    def take_snapshot(self, stage_name: str): ...
    def report_delta(self, start_stage: str, end_stage: str): ...

observer: Incomplete
