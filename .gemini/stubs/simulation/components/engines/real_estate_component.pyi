from modules.simulation.dtos.api import FirmConfigDTO as FirmConfigDTO
from typing import Any

class RealEstateUtilizationComponent:
    """
    TD-271: Converts firm-owned real estate into a production bonus.
    Applies production cost reduction based on owned space and market conditions.
    """
    def apply(self, owned_properties: list[int], config: FirmConfigDTO, firm_id: int, current_tick: int, market_data: dict[str, Any] | None = None) -> tuple[dict[str, Any] | None, int]: ...
