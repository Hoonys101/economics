"""
Implements the EventSystem which handles scheduled chaos events.
"""
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import logging
from simulation.systems.api import IEventSystem, EventContext
from simulation.finance.api import ISettlementSystem
from modules.system.api import DEFAULT_CURRENCY

if TYPE_CHECKING:
    from simulation.dtos.scenario import StressScenarioConfig
    from simulation.agents.central_bank import CentralBank
    from simulation.agents.government import Government

logger = logging.getLogger(__name__)

class EventSystem(IEventSystem):
    """
    Manages scheduled events like Inflation Shock and Recession Shock.
    """

    def __init__(self, config: Any, settlement_system: ISettlementSystem):
        self.config = config
        self.settlement_system = settlement_system

    def execute_scheduled_events(self, time: int, context: EventContext, config: "StressScenarioConfig") -> None:
        """
        Executes stress scenario triggers based on the provided configuration.
        """
        if not config or not config.is_active or time != config.start_tick:
            return

        logger.warning(f"🔥 STRESS_TEST: Activating '{config.scenario_name}' at Tick {time}!")
        households = context["households"]
        firms = context["firms"]

        # Access Government and Central Bank from context
        government = context.get("government")
        central_bank = context.get("central_bank")
        bank = context.get("bank")

        # Scenario 1: Hyperinflation (Demand-Pull Shock)
        if config.scenario_name == 'hyperinflation' and config.demand_shock_cash_injection > 0:
            if central_bank and self.settlement_system:
                for h in households:
                    assets_val = 0.0
                    if hasattr(h, 'wallet'):
                        assets_val = h.wallet.get_balance(DEFAULT_CURRENCY)
                    elif hasattr(h._econ_state, 'assets') and isinstance(h._econ_state.assets, dict):
                         assets_val = h._econ_state.assets.get(DEFAULT_CURRENCY, 0.0)
                    else:
                         # Fallback
                         assets_val = float(h._econ_state.assets) if hasattr(h._econ_state, 'assets') else 0.0

                    amount = assets_val * config.demand_shock_cash_injection
                    self.settlement_system.create_and_transfer(
                        source_authority=central_bank,
                        destination=h,
                        amount=amount,
                        reason="hyperinflation_stimulus",
                        tick=time
                    )
                logger.info(f"  -> Injected {config.demand_shock_cash_injection:.0%} cash into all households.")
            else:
                logger.warning("EventSystem: Missing CentralBank or SettlementSystem for Hyperinflation.")

        # Scenario 2: Deflationary Spiral (Asset Shock)
        if config.scenario_name == 'deflation' and config.asset_shock_reduction > 0:
            if central_bank and self.settlement_system:
                for agent in households + firms:
                    assets_val = 0.0
                    if hasattr(agent, 'wallet'):
                        assets_val = agent.wallet.get_balance(DEFAULT_CURRENCY)
                    elif hasattr(agent, 'assets') and isinstance(agent.assets, dict):
                        assets_val = agent.assets.get(DEFAULT_CURRENCY, 0.0)
                    elif hasattr(agent, 'assets'):
                        assets_val = float(agent.assets)

                    amount_to_destroy = assets_val * config.asset_shock_reduction
                    self.settlement_system.transfer_and_destroy(
                        source=agent,
                        sink_authority=central_bank,
                        amount=amount_to_destroy,
                        reason="deflationary_shock",
                        tick=time
                    )
                logger.info(f"  -> Reduced all agent assets by {config.asset_shock_reduction:.0%}.")
            else:
                logger.warning("EventSystem: Missing CentralBank or SettlementSystem for Deflation.")

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

            if config.monetary_shock_target_rate is not None and central_bank and bank:
                # Apply Monetary Shock: Increase Base Rate
                if hasattr(central_bank, "base_rate"):
                    central_bank.base_rate = config.monetary_shock_target_rate

                # Force Bank Rate directly
                if hasattr(bank, "update_base_rate"):
                    bank.update_base_rate(config.monetary_shock_target_rate)
                logger.info(f"  -> MONETARY SHOCK: Forced Bank Base Rate to {config.monetary_shock_target_rate}")

            if config.fiscal_shock_tax_rate is not None and government:
                # Apply Fiscal Shock: Increase Corporate Tax Rate
                if hasattr(government, "corporate_tax_rate"):
                    government.corporate_tax_rate = config.fiscal_shock_tax_rate
                    logger.info(f"  -> FISCAL SHOCK: Forced Corporate Tax Rate to {config.fiscal_shock_tax_rate}")

            # Phase 29: Dynamic Shock Parameters
            if config.base_interest_rate_multiplier is not None and central_bank and bank:
                # Apply Multiplier to existing rate
                current_rate = central_bank.base_rate if hasattr(central_bank, "base_rate") else bank.base_rate
                new_rate = current_rate * config.base_interest_rate_multiplier

                if hasattr(central_bank, "base_rate"):
                    central_bank.base_rate = new_rate
                if hasattr(bank, "update_base_rate"):
                    bank.update_base_rate(new_rate)
                logger.info(f"  -> MONETARY SHOCK: Multiplied Base Rate by {config.base_interest_rate_multiplier} to {new_rate:.4f}")

            if config.corporate_tax_rate_delta is not None and government:
                # Apply Delta to Corporate Tax Rate
                if hasattr(government, "corporate_tax_rate"):
                    old_rate = government.corporate_tax_rate
                    government.corporate_tax_rate += config.corporate_tax_rate_delta
                    logger.info(f"  -> FISCAL SHOCK: Increased Corporate Tax Rate by {config.corporate_tax_rate_delta} (From {old_rate} to {government.corporate_tax_rate})")
