from _typeshed import Incomplete

logger: Incomplete

class ShadowLogger:
    """
    WO-056: Stage 1 Shadow Mode Logger.
    Logs 'Invisible Hand' shadow calculations to a CSV file for analysis.
    """
    LOG_FILE: str
    HEADERS: Incomplete
    def __new__(cls): ...
    def log(self, tick: int, agent_id: int, agent_type: str, metric: str, current_value: float, shadow_value: float, details: str | None = ''):
        """
        Logs a single shadow metric record.
        """

def log_shadow(tick: int, agent_id: int, agent_type: str, metric: str, current_value: float, shadow_value: float, details: str = ''): ...
