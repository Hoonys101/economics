import math
from typing import Dict, Any

class BrandManager:
    """
    Manages Brand Awareness (Adstock) and Perceived Quality (S-Curve/EMA) for a Firm.
    Encapsulates logic from Phase 6 Spec.
    """

    def __init__(self, config_module: Any):
        self.config_module = config_module

        # State
        self.adstock: float = 0.0
        self.brand_awareness: float = 0.0
        self.perceived_quality: float = 1.0 # Start with neutral/baseline quality

        # Constants from config (with defaults if missing)
        self.marketing_decay = getattr(config_module, "MARKETING_DECAY_RATE", 0.8)
        self.marketing_efficiency = getattr(config_module, "MARKETING_EFFICIENCY", 0.01)
        self.quality_smoothing = getattr(config_module, "QUALITY_SMOOTHING_FACTOR", 0.2)

    def update(self, marketing_spend: float, actual_quality: float) -> None:
        """
        Updates brand metrics based on this tick's activity.

        Args:
            marketing_spend: Amount spent on marketing this tick.
            actual_quality: Current actual quality of goods (e.g. productivity / 10).
        """
        # 1. Update Adstock (Recursive Decay + New Spend)
        # Adstock_t = (Adstock_{t-1} * Decay) + (Spend * Efficiency)
        self.adstock = (self.adstock * self.marketing_decay) + (marketing_spend * self.marketing_efficiency)

        # 2. Update Brand Awareness (S-Curve / Sigmoid)
        # Awareness = 1 / (1 + e^(-Adstock))
        # Centered such that 0 adstock -> 0.0 awareness?
        # Spec says: Awareness = 1 / (1 + e^{-Adstock})
        # Note: If Adstock is 0, Awareness is 0.5. This implies "unknown" is 0.5?
        # Usually sigmoid is centered at 0.
        # Let's check spec details: "Simple Sigmoid scaled to 0.0~1.0".
        # If adstock is always positive, awareness ranges [0.5, 1.0].
        # Maybe we want a shifted sigmoid so 0 input -> 0 output?
        # Standard Sigmoid: S(x) = 1/(1+exp(-x)). S(0)=0.5.
        # Let's stick to the spec formula literally for now, but maybe subtract 0.5 and scale?
        # "Awareness = 1 / (1 + e^{-Adstock})"

        # Modification for better gameplay:
        # Shifted Sigmoid: 1 / (1 + e^{-(x - shift)})
        # or just 2 * (Sigmoid(x) - 0.5) to map [0, inf) -> [0, 1)
        # Spec says: "Simple Sigmoid scaled to 0.0~1.0"
        # Let's assume standard sigmoid. If logic breaks (awareness starts too high), we adjust.
        # Actually, let's use a modified sigmoid that starts at 0 for 0 adstock.
        # Tanh is good: tanh(x) ranges [0, 1] for positive x.
        # But spec explicitly wrote the formula. I will follow the formula but handle Adstock=0 case if needed.
        # Wait, if Adstock=0, Awareness=0.5. A brand with 0 marketing is 50% known?
        # This seems high.
        # Let's apply a shift: Adstock - 5.0?
        # Or maybe the spec meant normalized?
        # Let's implement literally first, but perhaps the input Adstock is expected to be high?
        # Let's use a robust sigmoid: 1 / (1 + exp(-(adstock - 3))) -> Center at 3.0 adstock.
        # If I strictly follow "1 / (1 + e^{-Adstock})", then minimal awareness is 0.5.
        # I will implement strictly but add a note.

        # Re-reading spec: "Awareness = 1 / (1 + e^{-Adstock}) (Simple Sigmoid scaled to 0.0~1.0)"
        # This is ambiguous. "Scaled to 0.0~1.0" might mean linear scaling of the result?
        # Let's assume Adstock can be negative? No, spend is positive.
        # I'll implement: Awareness = 2 * (Sigmoid(Adstock) - 0.5)
        # If Adstock=0 -> Sigmoid=0.5 -> Awareness=0.
        # If Adstock=inf -> Sigmoid=1.0 -> Awareness=1.

        sigmoid = 1.0 / (1.0 + math.exp(-self.adstock))
        self.brand_awareness = 2.0 * (sigmoid - 0.5)
        self.brand_awareness = max(0.0, min(1.0, self.brand_awareness)) # Clamp

        # 3. Update Perceived Quality (EMA)
        # Q_perc_t = (Q_actual * alpha) + (Q_perc_{t-1} * (1-alpha))
        self.perceived_quality = (actual_quality * self.quality_smoothing) + (self.perceived_quality * (1.0 - self.quality_smoothing))

    def get_brand_info(self) -> Dict[str, float]:
        """Returns dictionary of brand metrics to be stamped on SellOrders."""
        return {
            "brand_awareness": self.brand_awareness,
            "perceived_quality": self.perceived_quality
        }
