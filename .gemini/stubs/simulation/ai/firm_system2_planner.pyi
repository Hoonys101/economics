from _typeshed import Incomplete
from simulation.ai.enums import Personality as Personality
from typing import Any

logger: Incomplete

class FirmSystem2Planner:
    """
    Firm System 2 Planner (Phase 21).
    Responsible for long-term strategic guidance based on NPV projections.
    - Decides Target Automation Level.
    - Decides R&D Intensity.
    - Decides Expansion Mode (Organic vs M&A).
    """
    firm: Incomplete
    config: Incomplete
    logger: Incomplete
    horizon: Incomplete
    discount_rate: Incomplete
    calc_interval: Incomplete
    last_calc_tick: int
    cached_guidance: dict[str, Any]
    def __init__(self, firm: Any, config_module: Any) -> None: ...
    def project_future(self, current_tick: int, market_data: dict[str, Any], firm_state: Any | None = None) -> dict[str, Any]:
        """
        Projects future cash flows to determine strategic direction.
        Returns guidance dictionary.
        Uses firm_state (FirmStateDTO).
        """
