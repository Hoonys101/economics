from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any, List, Optional
from simulation.models import Order


if TYPE_CHECKING:
    from simulation.engine import Simulation
    from simulation.core_agents import Household

logger = logging.getLogger(__name__)

class HousingSystem:
    """
    Phase 22.5: Housing Market System
    Handles rent collection, maintenance, mortgages, foreclosures, and transactions.
    """

    def __init__(self, config_module: Any):
        self.config = config_module

    def process_housing(self, simulation: "Simulation"):
        """
        Processes mortgage payments, maintenance costs, rent collection, and eviction/foreclosure checks.
        Consolidated from Simulation._process_housing (Line 1221 in engine.py).
        """
        # 1. Process Bank/Mortgages
        for unit in simulation.real_estate_units:
            if unit.mortgage_id:
                loan = simulation.bank.loans.get(unit.mortgage_id)
                if loan and loan.is_active:
                    if loan.missed_payments >= 3:
                        # Foreclosure
                        old_owner_id = unit.owner_id
                        unit.owner_id = -1  # -1 is Bank/Govt
                        unit.mortgage_id = None
                        
                        # Evict Occupant (if owner was occupying)
                        if unit.occupant_id == old_owner_id:
                            unit.occupant_id = None
                            old_owner_agent = simulation.agents.get(old_owner_id)
                            if old_owner_agent and hasattr(old_owner_agent, "owned_properties"):
                                if unit.id in old_owner_agent.owned_properties:
                                    old_owner_agent.owned_properties.remove(unit.id)
                                if hasattr(old_owner_agent, "residing_property_id"):
                                    old_owner_agent.residing_property_id = None
                                    old_owner_agent.is_homeless = True
                                    
                        term_tx = simulation.bank.terminate_loan(loan.id)
                        if term_tx:
                             if hasattr(simulation, 'world_state'):
                                 simulation.world_state.transactions.append(term_tx)
                        
                        fire_sale_price = unit.estimated_value * 0.8
                        sell_order = Order(
                            agent_id=-1,
                            item_id=f"unit_{unit.id}",
                            price=fire_sale_price,
                            quantity=1.0,
                            market_id="housing",
                            order_type="SELL"
                        )
                        if "housing" in simulation.markets:
                            simulation.markets["housing"].place_order(sell_order, simulation.time)

        # 2. Rent & Maintenance
        settlement = getattr(simulation, 'settlement_system', None)

        for unit in simulation.real_estate_units:
            # A. Maintenance Cost (Owner pays)
            if unit.owner_id is not None and unit.owner_id != -1:
                owner = simulation.agents.get(unit.owner_id)
                if owner:
                    cost = unit.estimated_value * self.config.MAINTENANCE_RATE_PER_TICK
                    payable = min(cost, owner.assets)
                    if payable > 0 and settlement and simulation.government:
                        settlement.transfer(owner, simulation.government, payable, "housing_maintenance", tick=simulation.time)

            # B. Rent Collection (Tenant pays Owner)
            if unit.occupant_id is not None and unit.owner_id is not None:
                if unit.occupant_id == unit.owner_id:
                    continue

                tenant = simulation.agents.get(unit.occupant_id)
                owner = simulation.agents.get(unit.owner_id)

                if tenant and owner and tenant.is_active and owner.is_active:
                    rent = unit.rent_price
                    if tenant.assets >= rent:
                        if settlement:
                            settlement.transfer(tenant, owner, rent, "rent_payment", tick=simulation.time)
                    else:
                        # Eviction due to rent non-payment
                        logger.info(
                            f"EVICTION | Household {tenant.id} evicted from Unit {unit.id} due to non-payment.",
                            extra={"agent_id": tenant.id, "unit_id": unit.id}
                        )
                        unit.occupant_id = None
                        if hasattr(tenant, "residing_property_id"):
                            tenant.residing_property_id = None
                            tenant.is_homeless = True

    def apply_homeless_penalty(self, simulation: "Simulation"):
        """
        Applies survival penalties to homeless agents.
        """
        for hh in simulation.households:
            if hh.is_active:
                if hh.residing_property_id is None:
                    hh.is_homeless = True
                else:
                    hh.is_homeless = False

                if hh.is_homeless:
                    if "survival" not in hh.needs:
                        logger.error(f"CRITICAL: Household {hh.id} missing 'survival' need! Needs: {hh.needs.keys()}")
                        # Hotfix: Restore survival need
                        hh.needs["survival"] = 50.0

                    hh.needs["survival"] += self.config.HOMELESS_PENALTY_PER_TICK
                    logger.debug(
                        f"HOMELESS_PENALTY | Household {hh.id} survival need increased.",
                        extra={"agent_id": hh.id}
                    )

