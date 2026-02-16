from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import math
import logging

if TYPE_CHECKING:
    from modules.simulation.dtos.api import FirmConfigDTO
    from simulation.components.state.firm_state_models import SalesState

logger = logging.getLogger(__name__)

class BrandEngine:
    """
    Stateless engine for managing firm brand equity (Adstock, Awareness, Perceived Quality).
    Replaces stateful BrandManager.
    """

    def update(
        self,
        state: SalesState,
        config: FirmConfigDTO,
        marketing_spend: float,
        actual_quality: float,
        firm_id: int # For logging
    ) -> None:
        """
        Updates brand assets in the SalesState based on marketing spend and quality.
        """
        # 1. Adstock Update
        # Decay old adstock, add new spend (converted to adstock units)
        decay_rate = config.marketing_decay_rate
        efficiency = config.marketing_efficiency

        # Adstock = (Previous * Decay) + (Spend * Efficiency)
        state.adstock = (state.adstock * decay_rate) + (marketing_spend * efficiency)

        # 2. Awareness Calculation (Sigmoid/S-Curve)
        # Using simple 1 - exp(-adstock) as per Spec
        # Awareness approaches 1.0 as Adstock -> Infinity
        state.brand_awareness = 1.0 - math.exp(-state.adstock)

        # 3. Perceived Quality Update (EMA)
        # Q_perc_t = (Q_actual * alpha) + (Q_perc_t-1 * (1-alpha))
        alpha = config.perceived_quality_alpha

        # Ensure actual_quality is float
        if actual_quality is None:
            actual_quality = 0.0

        state.perceived_quality = (actual_quality * alpha) + (state.perceived_quality * (1.0 - alpha))

        logger.debug(
            f"BRAND_UPDATE | Firm {firm_id}: Spend={marketing_spend:.1f}, "
            f"Adstock={state.adstock:.3f}, Awareness={state.brand_awareness:.3f}, "
            f"ActQ={actual_quality:.2f}, PercQ={state.perceived_quality:.2f}",
            extra={"agent_id": firm_id, "tick": -1, "tags": ["brand"]}
        )
