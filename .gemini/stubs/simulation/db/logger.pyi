import types
from _typeshed import Incomplete
from typing import Any

logger: Incomplete

class SimulationLogger:
    db_path: Incomplete
    conn: Incomplete
    buffer: list[tuple]
    snapshot_buffer: list[tuple]
    run_id: int | None
    def __init__(self, db_path: str) -> None: ...
    def __enter__(self): ...
    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None) -> None: ...
    def log_thought(self, tick: int, agent_id: str, action: str, decision: str, reason: str, context: dict[str, Any]):
        """
        Logs an agent's thought process.
        """
    def log_snapshot(self, tick: int, snapshot_data: Any):
        """
        Logs a high-level snapshot of the simulation state.
        snapshot_data is expected to be an object (e.g. DTO) or dict with gdp, m2, cpi, transaction_count.
        """
    def flush(self) -> None:
        """
        Flushes buffered logs to the database in a single transaction.
        """
    def close(self) -> None: ...
