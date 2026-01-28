from __future__ import annotations
from typing import Dict, Any, Optional, TYPE_CHECKING
import math
import logging

if TYPE_CHECKING:
    from simulation.dtos.config_dtos import FirmConfigDTO

class BrandManager:
    """
    Manages a firm's intangible assets: Adstock, Brand Awareness, and Perceived Quality.
    Based on Phase 6 Spec.
    """
    def __init__(self, firm_id: int, config: FirmConfigDTO, logger: Optional[logging.Logger] = None):
        self.firm_id = firm_id
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        self.adstock = 0.0          # Marketing memory
        self.brand_awareness = 0.0  # 0.0 ~ 1.0 (S-curve of adstock)
        self.perceived_quality = 0.0 # Market perception weighting actual quality

    def update(self, marketing_spend: float, actual_quality: float) -> None:
        """
        Updates brand assets based on this tick's marketing spend and product quality.
        """
        # 1. Adstock Update
        # Decay old adstock, add new spend (converted to adstock units)
        decay_rate = self.config.marketing_decay_rate
        efficiency = self.config.marketing_efficiency
        
        # Adstock = (Previous * Decay) + (Spend * Efficiency)
        self.adstock = (self.adstock * decay_rate) + (marketing_spend * efficiency)

        # 2. Awareness Calculation (Sigmoid/S-Curve)
        # Using simple 1 - exp(-adstock) as per Spec
        # Awareness approaches 1.0 as Adstock -> Infinity
        self.brand_awareness = 1.0 - math.exp(-self.adstock)

        # 3. Perceived Quality Update (EMA)
        # Q_perc_t = (Q_actual * alpha) + (Q_perc_t-1 * (1-alpha))
        alpha = self.config.perceived_quality_alpha
        
        # Ensure actual_quality is float
        if actual_quality is None:
            actual_quality = 0.0

        self.perceived_quality = (actual_quality * alpha) + (self.perceived_quality * (1.0 - alpha))

        if self.logger:
             self.logger.debug(
                f"BRAND_UPDATE | Firm {self.firm_id}: Spend={marketing_spend:.1f}, "
                f"Adstock={self.adstock:.3f}, Awareness={self.brand_awareness:.3f}, "
                f"ActQ={actual_quality:.2f}, PercQ={self.perceived_quality:.2f}",
                extra={"agent_id": self.firm_id, "tick": -1, "tags": ["brand"]}
             )
