from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any, List, Optional, Dict
from uuid import uuid4, UUID
from simulation.models import Order
from modules.housing.dtos import (
    HousingPurchaseDecisionDTO,
    HousingTransactionSagaStateDTO
)
from modules.market.housing_purchase_api import (
    HousingPurchaseSagaDTO,
    HousingPurchaseSagaDataDTO,
    MortgageApplicationDTO
)
from modules.market.loan_api import MortgageApplicationRequestDTO


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
        self.pending_sagas: List[Dict[str, Any]] = []
        # Saga management moved to SettlementSystem

    def process_housing(self, simulation: "Simulation"):
        """
        Processes mortgage payments, maintenance costs, rent collection, and eviction/foreclosure checks.
        Consolidated from Simulation._process_housing (Line 1221 in engine.py).
        Also flushes queued housing transactions to SettlementSystem.
        """
        # 0. Flush Queued Sagas
        if self.pending_sagas:
            for req in self.pending_sagas:
                self._submit_saga_to_settlement(simulation, req['decision'], req['buyer_id'])
            self.pending_sagas.clear()

        # 1. Process Bank/Mortgages
        for unit in simulation.real_estate_units:
            if unit.mortgage_id:
                loan = simulation.bank.loans.get(unit.mortgage_id)
                if loan and loan.remaining_balance > 0:
                    if getattr(loan, 'missed_payments', 0) >= 3:
                        # Foreclosure
                        old_owner_id = unit.owner_id
                        unit.owner_id = -1  # -1 is Bank/Govt
                        # Clear mortgages (foreclosure)
                        unit.liens = [lien for lien in unit.liens if lien['lien_type'] != 'MORTGAGE']
                        
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
                        
                        fire_sale_discount = getattr(self.config, "FORECLOSURE_FIRE_SALE_DISCOUNT", 0.8)
                        fire_sale_price = unit.estimated_value * fire_sale_discount
                        sell_order = Order(
                            agent_id=-1,
                            side="SELL",
                            item_id=f"unit_{unit.id}",
                            quantity=1.0,
                            price_limit=fire_sale_price,
                            market_id="housing"
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

    def initiate_purchase(self, decision: HousingPurchaseDecisionDTO, buyer_id: int):
        """
        Starts a new housing transaction saga.
        Called by DecisionUnit (or via orchestration).
        """
        # Queue for processing in next tick cycle (or later in this tick if Phase 5 runs)
        self.pending_sagas.append({
            "decision": decision,
            "buyer_id": buyer_id
        })
        logger.info(f"SAGA_QUEUED | Saga queued for buyer {buyer_id} property {decision['target_property_id']}")

    def _calculate_total_monthly_debt_payments(self, agent_id: int, bank_service: Any) -> float:
        """
        Helper to calculate total monthly debt payments for an agent.
        Iterates over all loans and sums their monthly obligations.
        """
        existing_debt_payments = 0.0
        if bank_service and hasattr(bank_service, 'get_debt_status'):
             try:
                 debt_status = bank_service.get_debt_status(str(agent_id))
                 # Calculate total monthly payment from loans
                 # Assuming loans have 'outstanding_balance' and 'interest_rate'
                 for loan in debt_status.get('loans', []):
                     # Estimate monthly payment
                     balance = loan.get('outstanding_balance', 0.0)
                     rate = loan.get('interest_rate', 0.05)
                     # Default assumption if not available (ideally loan DTO has remaining ticks)
                     # Using 300 (30 years * 10 ticks/year?) or just a standard constant.
                     # Let's use 360 ticks (standard 30 year monthly).
                     term = 360

                     monthly_rate = rate / 12.0
                     if monthly_rate == 0:
                         payment = balance / term
                     else:
                         payment = balance * (monthly_rate * (1 + monthly_rate)**term) / ((1 + monthly_rate)**term - 1)
                     existing_debt_payments += payment
             except Exception as e:
                 logger.warning(f"Failed to fetch debt status for {agent_id}: {e}")
        return existing_debt_payments

    def _submit_saga_to_settlement(self, simulation: "Simulation", decision: HousingPurchaseDecisionDTO, buyer_id: int):
        saga_id = str(uuid4())

        offer_price = decision['offer_price']
        down_payment = decision['down_payment_amount']
        principal = offer_price - down_payment
        prop_id = decision['target_property_id']

        # Gather data for Mortgage Application
        household = simulation.agents.get(buyer_id)
        annual_income = 0.0

        if household:
             # Logic to estimate income
             if hasattr(household, 'current_wage'):
                  ticks_per_year = getattr(self.config, 'TICKS_PER_YEAR', 100)
                  # Assuming current_wage is per tick? Or monthly?
                  # Household model usually has current_wage.
                  annual_income = household.current_wage * ticks_per_year

        # [TD-206] Use helper for precise debt payments
        existing_debt_payments = self._calculate_total_monthly_debt_payments(buyer_id, simulation.bank)

        # Resolve seller
        seller_id = -1
        # Need to access registry to find owner
        units = getattr(simulation, 'real_estate_units', [])
        unit = next((u for u in units if u.id == prop_id), None)
        if unit:
             seller_id = unit.owner_id

        # Get Loan Term from Config
        housing_config = getattr(self.config, 'housing', {})
        # Support object or dict access
        if isinstance(housing_config, dict):
             loan_term = housing_config.get('mortgage_term_ticks', 300)
        else:
             loan_term = getattr(housing_config, 'mortgage_term_ticks', 300)

        # [TD-206] Use MortgageApplicationRequestDTO
        mortgage_app = MortgageApplicationRequestDTO(
            applicant_id=buyer_id,
            requested_principal=principal,
            property_id=prop_id,
            property_value=offer_price,
            applicant_monthly_income=annual_income / 12.0, # Convert annual to monthly
            existing_monthly_debt_payments=existing_debt_payments,
            loan_term=loan_term
        )

        saga_data = HousingPurchaseSagaDataDTO(
            household_id=buyer_id,
            property_id=prop_id,
            offer_price=offer_price,
            down_payment=down_payment,
            mortgage_application=mortgage_app,
            approved_loan_id=None,
            seller_id=seller_id
        )

        saga = HousingPurchaseSagaDTO(
            saga_id=saga_id,
            saga_type="HOUSING_PURCHASE",
            status="STARTED",
            current_step=0,
            data=saga_data,
            start_tick=simulation.time
        )

        if simulation.settlement_system:
             # Assuming we updated SettlementSystem to have submit_saga
             if hasattr(simulation.settlement_system, 'submit_saga'):
                 simulation.settlement_system.submit_saga(saga)
             else:
                 logger.error("SettlementSystem does not support submit_saga")

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
