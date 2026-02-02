import logging
from typing import Optional, Dict, List, Any
from simulation.core_agents import Household
from simulation.agents.government import Government
from simulation.dtos.settlement_dtos import EstateSettlementSaga, EstateValuationDTO

logger = logging.getLogger(__name__)

class InheritanceManager:
    """
    Phase 22 (WO-049): Legacy Protocol
    Handles Death, Valuation, Taxation (Liquidation), and Transfer.
    Ensures 'Zero Leak' and atomic settlement via Saga pattern (TD-160).
    """
    def __init__(self, config_module: Any):
        self.config_module = config_module
        self.logger = logging.getLogger("simulation.systems.inheritance_manager")

    def process_death(self, deceased: Household, government: Government, simulation: Any) -> EstateSettlementSaga:
        """
        Creates an atomic settlement saga for the deceased agent.
        Does NOT execute any transactions.

        Args:
            deceased: The agent who died.
            government: The entity collecting tax.
            simulation: Access to markets/registry for valuation (SimulationState).

        Returns:
            EstateSettlementSaga: The saga object containing valuation and instructions.
        """
        current_tick = simulation.time

        self.logger.info(
            f"INHERITANCE_START | Processing death for Household {deceased.id}. Assets: {deceased._econ_state.assets:.2f}",
            extra={"agent_id": deceased.id, "tags": ["inheritance", "death"]}
        )

        # 1. Valuation (Read-only)
        cash = round(deceased._econ_state.assets, 2)

        real_estate_value = 0.0
        property_holdings = []
        deceased_units = [u for u in simulation.real_estate_units if u.owner_id == deceased.id]
        for unit in deceased_units:
            real_estate_value += unit.estimated_value
            property_holdings.append(unit.id)
        real_estate_value = round(real_estate_value, 2)

        stock_value = 0.0
        stock_holdings = {}
        if simulation.stock_market:
            for firm_id, share in deceased._econ_state.portfolio.holdings.items():
                price = simulation.stock_market.get_daily_avg_price(firm_id)
                if price <= 0:
                    price = share.acquisition_price
                # Round price to prevent dust
                price = round(price, 2)

                # Calculate value
                holding_value = round(share.quantity * price, 2)
                stock_value += holding_value
                stock_holdings[firm_id] = share.quantity

        stock_value = round(stock_value, 2)
        total_wealth = round(cash + real_estate_value + stock_value, 2)

        # 2. Calculate Tax
        tax_rate = getattr(self.config_module, "INHERITANCE_TAX_RATE", 0.4)
        deduction = getattr(self.config_module, "INHERITANCE_DEDUCTION", 10000.0)
        taxable_base = max(0.0, total_wealth - deduction)
        tax_amount = round(taxable_base * tax_rate, 2)

        self.logger.info(
            f"ESTATE_VALUATION | Agent {deceased.id}: Cash={cash:.2f}, RE={real_estate_value:.2f}, Stock={stock_value:.2f} -> Total={total_wealth:.2f}. Tax={tax_amount:.2f}",
            extra={"agent_id": deceased.id, "total_wealth": total_wealth, "tax_amount": tax_amount}
        )

        # 3. Identify Heirs
        heirs = []
        for child_id in deceased._bio_state.children_ids:
            child = simulation.agents.get(child_id)
            if child and child._bio_state.is_active:
                heirs.append(child.id)

        # 4. Construct DTOs
        valuation = EstateValuationDTO(
            cash=cash,
            real_estate_value=real_estate_value,
            stock_value=stock_value,
            total_wealth=total_wealth,
            tax_due=tax_amount,
            stock_holdings=stock_holdings,
            property_holdings=property_holdings
        )

        saga = EstateSettlementSaga(
            deceased_id=deceased.id,
            heir_ids=heirs,
            government_id=government.id,
            valuation=valuation,
            current_tick=current_tick
        )

        return saga
