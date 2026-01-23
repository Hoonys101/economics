import csv
import os
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ShadowLogger:
    """
    WO-056: Stage 1 Shadow Mode Logger.
    Logs 'Invisible Hand' shadow calculations to a CSV file for analysis.
    """

    _instance = None
    LOG_FILE = "logs/shadow_hand_stage1.csv"
    HEADERS = [
        "tick",
        "agent_id",
        "agent_type",
        "metric",
        "current_value",
        "shadow_value",
        "details",
    ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ShadowLogger, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initializes the CSV file with headers."""
        self.initialized = True
        try:
            # Create logs directory if it doesn't exist (redundant if handled externally but safe)
            os.makedirs(os.path.dirname(self.LOG_FILE), exist_ok=True)

            # Initialize file with headers
            with open(self.LOG_FILE, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(self.HEADERS)

            logger.info(f"ShadowLogger initialized at {self.LOG_FILE}")
        except Exception as e:
            logger.error(f"Failed to initialize ShadowLogger: {e}")

    def log(
        self,
        tick: int,
        agent_id: int,
        agent_type: str,
        metric: str,
        current_value: float,
        shadow_value: float,
        details: Optional[str] = "",
    ):
        """
        Logs a single shadow metric record.
        """
        try:
            with open(self.LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        tick,
                        agent_id,
                        agent_type,
                        metric,
                        f"{current_value:.4f}",
                        f"{shadow_value:.4f}",
                        details,
                    ]
                )
        except Exception as e:
            # Suppress errors to prevent crashing the simulation, but log error
            logger.error(f"ShadowLogger write failed: {e}")


# Global instance helper
def log_shadow(
    tick: int,
    agent_id: int,
    agent_type: str,
    metric: str,
    current_value: float,
    shadow_value: float,
    details: str = "",
):
    ShadowLogger().log(
        tick, agent_id, agent_type, metric, current_value, shadow_value, details
    )
