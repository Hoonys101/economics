from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any, List, Optional, Dict, cast
from uuid import uuid4, UUID
from dataclasses import asdict, is_dataclass

from simulation.models import Order
from modules.market.housing_planner_api import HousingDecisionDTO as HousingPurchaseDecisionDTO
from modules.finance.sagas.housing_api import HousingTransactionSagaStateDTO, HousingSagaAgentContext
from modules.simulation.api import HouseholdSnapshotDTO
from modules.finance.api import MortgageApplicationDTO
from modules.system.api import DEFAULT_CURRENCY

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

    def process_housing(self, simulation: 'Simulation'):
        """
        Processes mortgage payments, maintenance costs, rent collection, and eviction/foreclosure checks.
        Consolidated from Simulation._process_housing (Line 1221 in engine.py).
        Also flushes queued housing transactions to SettlementSystem.
        """
        if self.pending_sagas:
            for req in self.pending_sagas:
                self._submit_saga_to_settlement(simulation, req['decision'], req['buyer_id'])
            self.pending_sagas.clear()

        # Iterate over copy to allow modification
        for unit in list(simulation.real_estate_units):
            if unit.mortgage_id:
                loan = simulation.bank.loans.get(unit.mortgage_id) if simulation.bank and hasattr(simulation.bank, 'loans') else None
                # If bank logic is different, we might need IBankService methods.
                # Assuming simulation.bank exposes loans dict for now or legacy access.

                if loan and loan.remaining_balance > 0:
                    missed = getattr(loan, 'missed_payments', 0)
                    if missed >= 3:
                        old_owner_id = unit.owner_id
                        unit.owner_id = -1
                        unit.liens = [lien for lien in unit.liens if lien.get('lien_type') != 'MORTGAGE'] if unit.liens else []

                        if unit.occupant_id == old_owner_id:
                            unit.occupant_id = None
                            old_owner_agent = simulation.agents.get(old_owner_id)
                            if old_owner_agent:
                                if hasattr(old_owner_agent, 'owned_properties') and unit.id in old_owner_agent.owned_properties:
                                    old_owner_agent.owned_properties.remove(unit.id)
                                if hasattr(old_owner_agent, 'residing_property_id'):
                                    old_owner_agent.residing_property_id = None
                                    old_owner_agent.is_homeless = True

                        # Terminate Loan
                        term_tx = None
                        if hasattr(simulation.bank, 'terminate_loan'):
                            term_tx = simulation.bank.terminate_loan(loan.id)

                        # Logging transaction manually (Legacy support, though ideally strict protocol)
                        if term_tx and hasattr(simulation, 'world_state'):
                             simulation.world_state.transactions.append(term_tx)

                        fire_sale_discount = getattr(self.config, 'FORECLOSURE_FIRE_SALE_DISCOUNT', 0.8)
                        fire_sale_price = unit.estimated_value * fire_sale_discount
                        sell_order = Order(
                            agent_id=-1,
                            side='SELL',
                            item_id=f'unit_{unit.id}',
                            quantity=1.0,
                            price_pennies=int(fire_sale_price),
                            price_limit=fire_sale_price / 100.0,
                            market_id='housing'
                        )
                        if 'housing' in simulation.markets:
                            simulation.markets['housing'].place_order(sell_order, simulation.time)

        settlement = getattr(simulation, 'settlement_system', None)

        # Maintenance Costs
        for unit in simulation.real_estate_units:
            if unit.owner_id is not None and unit.owner_id != -1:
                owner = simulation.agents.get(unit.owner_id)
                if owner:
                    cost = unit.estimated_value * self.config.MAINTENANCE_RATE_PER_TICK
                    owner_assets = owner.assets
                    if isinstance(owner_assets, dict):
                        owner_assets = owner_assets.get(DEFAULT_CURRENCY, 0.0)
                    else:
                        owner_assets = float(owner_assets)

                    payable = min(cost, owner_assets)
                    if payable > 0 and settlement and hasattr(simulation, 'government') and simulation.government:
                        settlement.transfer(owner, simulation.government, int(payable), 'housing_maintenance', tick=simulation.time, currency=DEFAULT_CURRENCY)

            # Rent Collection
            if unit.occupant_id is not None and unit.owner_id is not None:
                if unit.occupant_id == unit.owner_id:
                    continue
                tenant = simulation.agents.get(unit.occupant_id)
                owner = simulation.agents.get(unit.owner_id)

                if tenant and owner and tenant.is_active and owner.is_active:
                    rent = unit.rent_price
                    tenant_assets = tenant.assets
                    if isinstance(tenant_assets, dict):
                        tenant_assets = tenant_assets.get(DEFAULT_CURRENCY, 0.0)
                    else:
                        tenant_assets = float(tenant_assets)

                    if tenant_assets >= rent:
                        if settlement:
                            settlement.transfer(tenant, owner, int(rent), 'rent_payment', tick=simulation.time, currency=DEFAULT_CURRENCY)
                    else:
                        logger.info(f'EVICTION | Household {tenant.id} evicted from Unit {unit.id} due to non-payment.', extra={'agent_id': tenant.id, 'unit_id': unit.id})
                        unit.occupant_id = None
                        if hasattr(tenant, 'residing_property_id'):
                            tenant.residing_property_id = None
                            tenant.is_homeless = True

    def initiate_purchase(self, decision: HousingPurchaseDecisionDTO, buyer_id: int):
        """
        Starts a new housing transaction saga.
        Called by DecisionUnit (or via orchestration).
        """
        # decision is now a dataclass, but check type to be safe or use getattr
        self.pending_sagas.append({'decision': decision, 'buyer_id': buyer_id})
        target_id = decision.target_property_id if is_dataclass(decision) else decision['target_property_id']
        logger.info(f"SAGA_QUEUED | Saga queued for buyer {buyer_id} property {target_id}")

    def _calculate_total_monthly_debt_payments(self, agent_id: int, bank_service: Any) -> float:
        """
        Helper to calculate total monthly debt payments for an agent.
        Iterates over all loans and sums their monthly obligations.
        """
        existing_debt_payments = 0.0
        if bank_service and hasattr(bank_service, 'get_debt_status'):
            try:
                debt_status = bank_service.get_debt_status(str(agent_id))
                loans = []
                if is_dataclass(debt_status):
                    loans = debt_status.loans
                elif isinstance(debt_status, dict):
                    loans = debt_status.get('loans', [])

                for loan in loans:
                    balance = 0.0
                    rate = 0.05
                    if is_dataclass(loan):
                        balance = loan.outstanding_balance
                        rate = loan.interest_rate
                    elif isinstance(loan, dict):
                        balance = loan.get('outstanding_balance', 0.0)
                        rate = loan.get('interest_rate', 0.05)

                    term = 360
                    monthly_rate = rate / 12.0
                    if monthly_rate == 0:
                        payment = balance / term
                    else:
                        payment = balance * (monthly_rate * (1 + monthly_rate) ** term) / ((1 + monthly_rate) ** term - 1)
                    existing_debt_payments += payment
            except Exception as e:
                logger.warning(f'Failed to fetch debt status for {agent_id}: {e}')
        return existing_debt_payments

    def _submit_saga_to_settlement(self, simulation: 'Simulation', decision: HousingPurchaseDecisionDTO, buyer_id: int):
        saga_id = uuid4()

        # Access dataclass fields
        if is_dataclass(decision):
            offer_price = decision.offer_price
            down_payment = decision.down_payment_amount
            prop_id = decision.target_property_id
        else:
             # Fallback if dictionary
            offer_price = decision['offer_price']
            down_payment = decision['down_payment_amount']
            prop_id = decision['target_property_id']

        principal = offer_price - down_payment

        household = simulation.agents.get(buyer_id)
        annual_income = 0.0
        cash_balance = 0.0
        credit_score = 0.0

        if household:
            if hasattr(household, 'current_wage'):
                ticks_per_year = getattr(self.config, 'TICKS_PER_YEAR', 100)
                annual_income = household.current_wage * ticks_per_year

            if isinstance(household.assets, dict):
                cash_balance = household.assets.get(DEFAULT_CURRENCY, 0.0)
            else:
                cash_balance = float(household.assets)

            if hasattr(household, 'credit_score'):
                credit_score = getattr(household, 'credit_score')

        existing_debt_payments = self._calculate_total_monthly_debt_payments(buyer_id, simulation.bank)

        buyer_snapshot = HouseholdSnapshotDTO(
            household_id=str(buyer_id),
            cash=cash_balance,
            income=annual_income,
            credit_score=credit_score,
            existing_debt=existing_debt_payments,
            assets_value=cash_balance
        )

        seller_id = -1
        units = getattr(simulation, 'real_estate_units', [])
        unit = next((u for u in units if u.id == prop_id), None)
        if unit:
            seller_id = unit.owner_id

        housing_config = getattr(self.config, 'housing', {})
        if isinstance(housing_config, dict):
            loan_term = housing_config.get('mortgage_term_ticks', 300)
        else:
            loan_term = getattr(housing_config, 'mortgage_term_ticks', 300)

        mortgage_app = MortgageApplicationDTO(
            applicant_id=buyer_id,
            requested_principal=principal,
            purpose='MORTGAGE',
            property_id=prop_id,
            property_value=offer_price,
            applicant_monthly_income=annual_income / 12.0,
            existing_monthly_debt_payments=existing_debt_payments,
            loan_term=loan_term
        )

        seller_context = HousingSagaAgentContext(
            id=seller_id,
            monthly_income=0.0,
            existing_monthly_debt=0.0
        )

        saga = HousingTransactionSagaStateDTO(
            saga_id=saga_id,
            status='INITIATED',
            buyer_context=buyer_snapshot,
            seller_context=seller_context,
            property_id=prop_id,
            offer_price=offer_price,
            down_payment_amount=down_payment,
            loan_application=mortgage_app,
            mortgage_approval=None,
            staged_loan_id=None,
            error_message=None,
            last_processed_tick=0,
            logs=[]
        )

        if hasattr(simulation, 'saga_orchestrator') and simulation.saga_orchestrator:
            simulation.saga_orchestrator.submit_saga(saga)
        elif simulation.settlement_system and hasattr(simulation.settlement_system, 'submit_saga'):
            simulation.settlement_system.submit_saga(saga)
        else:
            logger.error('No Saga Orchestrator available to submit housing saga.')

    def apply_homeless_penalty(self, simulation: 'Simulation'):
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
                    if 'survival' not in hh.needs:
                        logger.error(f"CRITICAL: Household {hh.id} missing 'survival' need! Needs: {hh.needs.keys()}")
                        hh.needs['survival'] = 50.0
                    hh.needs['survival'] += self.config.HOMELESS_PENALTY_PER_TICK
                    logger.debug(f'HOMELESS_PENALTY | Household {hh.id} survival need increased.', extra={'agent_id': hh.id})
