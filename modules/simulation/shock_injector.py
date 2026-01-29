from __future__ import annotations
from typing import Any, Dict, Optional
import logging
from modules.simulation.api import ShockConfigDTO

logger = logging.getLogger(__name__)

class ShockInjector:
    def __init__(self, config: ShockConfigDTO, simulation: Any):
        self._config = config
        self._simulation = simulation
        self._original_tfp_values: Dict[int, float] = {}

    def apply(self, current_tick: int) -> None:
        is_shock_active = self._config["shock_start_tick"] <= current_tick < self._config["shock_end_tick"]

        if is_shock_active:
            # 1. Capture original values if not already done
            if not self._original_tfp_values:
                # We access firms via world_state delegation on simulation
                # simulation.firms is List[Firm]
                for firm in self._simulation.firms:
                    self._original_tfp_values[firm.id] = firm.productivity_factor

                logger.warning(
                    f"SHOCK_START | TFP Shock activated at tick {current_tick}. "
                    f"Captured {len(self._original_tfp_values)} firms. "
                    f"Target TFP: {self._config['baseline_tfp'] * self._config['tfp_multiplier']:.2f}",
                    extra={"tick": current_tick}
                )

            # 2. Apply shock (Force set every tick to override drift/R&D)
            new_tfp = self._config["baseline_tfp"] * self._config["tfp_multiplier"]
            for firm in self._simulation.firms:
                # Direct attribute assignment as confirmed in Firm class
                firm.productivity_factor = new_tfp

        else:
            # 3. Restore values if we have captured data (Shock just ended)
            if self._original_tfp_values:
                for firm in self._simulation.firms:
                    if firm.id in self._original_tfp_values:
                        firm.productivity_factor = self._original_tfp_values[firm.id]
                    else:
                        # Fallback for firms created during shock
                        # Restore to baseline_tfp as a safe default
                        firm.productivity_factor = self._config["baseline_tfp"]

                logger.warning(
                    f"SHOCK_END | TFP Shock deactivated at tick {current_tick}. "
                    f"Restored {len(self._original_tfp_values)} firms.",
                    extra={"tick": current_tick}
                )

                self._original_tfp_values.clear()
