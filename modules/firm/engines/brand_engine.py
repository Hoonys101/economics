from __future__ import annotations
from typing import TYPE_CHECKING
import math
import logging
from modules.firm.api import IBrandEngine, BrandMetricsDTO
from modules.simulation.dtos.api import SalesStateDTO

if TYPE_CHECKING:
    from modules.simulation.dtos.api import FirmConfigDTO

logger = logging.getLogger(__name__)

class BrandEngine(IBrandEngine):
    """
    Stateless engine for managing firm brand equity (Adstock, Awareness, Perceived Quality).
    Replaces stateful BrandManager.
    """

    def update(
        self,
        state: SalesStateDTO,
        config: FirmConfigDTO,
        marketing_spend: float,
        actual_quality: float,
        firm_id: int # For logging
    ) -> BrandMetricsDTO:
        """
        Calculates updated brand metrics based on marketing spend and quality.
        """
        # 1. Adstock Update
        # Decay old adstock, add new spend (converted to adstock units)
        decay_rate = config.marketing_decay_rate
        efficiency = config.marketing_efficiency

        # Access from DTO (now has adstock)
        current_adstock = state.adstock

        # Adstock = (Previous * Decay) + (Spend * Efficiency)
        new_adstock = (current_adstock * decay_rate) + (marketing_spend * efficiency)

        # 2. Awareness Calculation (Sigmoid/S-Curve)
        # Using simple 1 - exp(-adstock) as per Spec
        # Awareness approaches 1.0 as Adstock -> Infinity
        new_awareness = 1.0 - math.exp(-new_adstock)

        # 3. Perceived Quality Update (EMA)
        # Q_perc_t = (Q_actual * alpha) + (Q_perc_t-1 * (1-alpha))
        alpha = config.perceived_quality_alpha

        # Ensure actual_quality is float
        if actual_quality is None:
            actual_quality = 0.0

        new_perceived_quality = (actual_quality * alpha) + (state.perceived_quality * (1.0 - alpha))

        logger.debug(
            f"BRAND_UPDATE | Firm {firm_id}: Spend={marketing_spend:.1f}, "
            f"Adstock={new_adstock:.3f}, Awareness={new_awareness:.3f}, "
            f"ActQ={actual_quality:.2f}, PercQ={new_perceived_quality:.2f}",
            extra={"agent_id": firm_id, "tick": -1, "tags": ["brand"]}
        )

        return BrandMetricsDTO(
            adstock=new_adstock,
            brand_awareness=new_awareness,
            perceived_quality=new_perceived_quality
        )
