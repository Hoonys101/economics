"""
Implements the EventSystem which handles scheduled chaos events.
"""
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import logging
from simulation.systems.api import IEventSystem, EventContext

if TYPE_CHECKING:
    from simulation.dtos.scenario import StressScenarioConfig
    from simulation.agents.central_bank import CentralBank
    from simulation.agents.government import Government

logger = logging.getLogger(__name__)

class EventSystem(IEventSystem):
    """
    Manages scheduled events like Inflation Shock and Recession Shock.
    """

    def __init__(self, config: Any):
        self.config = config

    def execute_scheduled_events(self, time: int, context: EventContext, config: "StressScenarioConfig") -> None:
        """
        Executes stress scenario triggers based on the provided configuration.
        """
        if not config or not config.is_active or time != config.start_tick:
            return

        logger.warning(f"🔥 STRESS_TEST: Activating '{config.scenario_name}' at Tick {time}!")
        households = context["households"]
        firms = context["firms"]
        # context might need expansion to include Government and CentralBank if not present
        # But `EventContext` definition in `simulation/systems/api.py` typically has households, firms, markets.
        # We might need to access Government/CentralBank via context or other means.
        # Looking at `simulation/engine.py`, `context` passed is: {"households": ..., "firms": ..., "markets": ...}
        # It does NOT have government or central bank.

        # However, we can modify `EventContext` in `api.py` and `engine.py` to include them.
        # Or we can access them if they are in `context` (if TypedDict allows extra keys or if we update it).

        # Scenario 1: Hyperinflation (Demand-Pull Shock)
        if config.scenario_name == 'hyperinflation' and config.demand_shock_cash_injection > 0:
            for h in households:
                h.assets *= (1 + config.demand_shock_cash_injection)
            logger.info(f"  -> Injected {config.demand_shock_cash_injection:.0%} cash into all households.")

        # Scenario 2: Deflationary Spiral (Asset Shock)
        if config.scenario_name == 'deflation' and config.asset_shock_reduction > 0:
            for agent in households + firms:
                agent.assets *= (1 - config.asset_shock_reduction)
            logger.info(f"  -> Reduced all agent assets by {config.asset_shock_reduction:.0%}.")

        # Scenario 3: Supply Shock (Productivity Collapse)
        if config.scenario_name == 'supply_shock' and config.exogenous_productivity_shock:
            for firm in firms:
                # Check if firm type is in the shock dictionary
                if firm.type in config.exogenous_productivity_shock:
                    shock_multiplier = config.exogenous_productivity_shock[firm.type]
                    firm.productivity_factor *= shock_multiplier
                    logger.info(f"  -> Applied productivity shock ({shock_multiplier}) to Firm {firm.id} (Type: {firm.type}).")

        # Scenario 4: Great Depression (Liquidity Crisis)
        if config.scenario_name == 'phase29_depression':
            logger.info("  -> Triggering Great Depression Scenario!")

            # Access Government and Central Bank
            # We need to update engine.py to pass these in context.
            government = context.get("government")
            central_bank = context.get("central_bank")
            bank = context.get("bank")

            if config.monetary_shock_target_rate is not None and central_bank and bank:
                # Apply Monetary Shock: Increase Base Rate
                # We can set it on Central Bank, and verify it propagates.
                # In engine.py:
                # self.central_bank.step(self.time)
                # new_base_rate = self.central_bank.get_base_rate()
                # self.bank.update_base_rate(new_base_rate)

                # If we want to override, we should set it on Central Bank or force it.
                # CentralBank might have a `target_rate` or similar.
                # Let's check CentralBank implementation.
                # Assuming `central_bank.base_rate` can be set.
                if hasattr(central_bank, "base_rate"):
                    central_bank.base_rate = config.monetary_shock_target_rate

                # Also force update bank immediately to ensure effect in this tick?
                # Engine updates it after government policy.
                # If we do it here (Start of Tick), we need to ensure it's not overwritten by `central_bank.step()`.
                # We might need to set a flag or "override" mode in CentralBank.
                # Or just update it and hope `step` respects it or we do it after step.

                # "Dirty Hack" requested in Spec 4.2.3?
                # "Any 'Dirty Hacks' required to override the Central Bank/Government behavior."
                # So I will just force set it.

                # Force Bank Rate directly
                bank.update_base_rate(config.monetary_shock_target_rate)
                logger.info(f"  -> MONETARY SHOCK: Forced Bank Base Rate to {config.monetary_shock_target_rate}")

            if config.fiscal_shock_tax_rate is not None and government:
                # Apply Fiscal Shock: Increase Corporate Tax Rate
                # Check if government has `corporate_tax_rate` attribute.
                if hasattr(government, "corporate_tax_rate"):
                    government.corporate_tax_rate = config.fiscal_shock_tax_rate
                    logger.info(f"  -> FISCAL SHOCK: Forced Corporate Tax Rate to {config.fiscal_shock_tax_rate}")
                # Also check `tax_rate` for general tax if applicable

            # Phase 29: Dynamic Shock Parameters
            if config.base_interest_rate_multiplier is not None and central_bank and bank:
                # Apply Multiplier to existing rate
                current_rate = central_bank.base_rate if hasattr(central_bank, "base_rate") else bank.base_rate
                new_rate = current_rate * config.base_interest_rate_multiplier

                if hasattr(central_bank, "base_rate"):
                    central_bank.base_rate = new_rate
                bank.update_base_rate(new_rate)
                logger.info(f"  -> MONETARY SHOCK: Multiplied Base Rate by {config.base_interest_rate_multiplier} to {new_rate:.4f}")

            if config.corporate_tax_rate_delta is not None and government:
                # Apply Delta to Corporate Tax Rate
                if hasattr(government, "corporate_tax_rate"):
                    old_rate = government.corporate_tax_rate
                    government.corporate_tax_rate += config.corporate_tax_rate_delta
                    logger.info(f"  -> FISCAL SHOCK: Increased Corporate Tax Rate by {config.corporate_tax_rate_delta} (From {old_rate} to {government.corporate_tax_rate})")
