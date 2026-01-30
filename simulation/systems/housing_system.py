from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any, List, Optional
from simulation.models import Order, Transaction
from simulation.agents.government import Government
from modules.finance.api import BorrowerProfileDTO


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
                                    
                        simulation.bank.terminate_loan(loan.id)
                        
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

    def process_transaction(self, tx: Transaction, simulation: "Simulation"):
        """
        Handles the logic for a housing market transaction.
        Consolidated from Simulation._process_housing_transaction (Line 1539 in engine.py).
        """
        if not hasattr(simulation, "settlement_system") or not simulation.settlement_system:
             logger.error("HOUSING | No SettlementSystem found. Aborting transaction.")
             return

        try:
            unit_id = int(tx.item_id.split("_")[1])
            unit = next((u for u in simulation.real_estate_units if u.id == unit_id), None)
            
            if not unit:
                logger.warning(f"HOUSING | Unit {tx.item_id} not found.")
                return

            buyer = simulation.agents.get(tx.buyer_id)
            seller = simulation.agents.get(tx.seller_id)

            if not buyer or not seller:
                return

            # 1. Mortgage Logic
            ltv_ratio = getattr(self.config, "MORTGAGE_LTV_RATIO", 0.8)
            mortgage_term = getattr(self.config, "MORTGAGE_TERM_TICKS", 300)
            mortgage_rate = getattr(self.config, "MORTGAGE_INTEREST_RATE", 0.05)
            
            trade_value = tx.price * tx.quantity
            loan_id = None
            loan_amount = 0.0

            if hasattr(buyer, "owned_properties"): # Household check
                loan_amount = trade_value * ltv_ratio

                # WO-078: Construct BorrowerProfileDTO
                gross_income = 0.0
                if hasattr(buyer, "current_wage"):
                    # Estimate Monthly Income using Configurable Parameters
                    work_hours = getattr(self.config, "WORK_HOURS_PER_DAY", 8.0)
                    ticks_per_year = getattr(self.config, "TICKS_PER_YEAR", 100.0)
                    ticks_per_month = ticks_per_year / 12.0

                    gross_income = buyer.current_wage * work_hours * ticks_per_month

                existing_debt_payments = 0.0
                try:
                    debt_status = simulation.bank.get_debt_status(buyer.id)
                    total_debt = debt_status.get("total_outstanding_debt", 0.0)
                    # Estimate monthly payment (approx 1% of principal as placeholder if term unknown)
                    monthly_payment_rate = getattr(self.config, "ESTIMATED_DEBT_PAYMENT_RATIO", 0.01)
                    existing_debt_payments = total_debt * monthly_payment_rate
                except Exception:
                    pass

                borrower_profile = BorrowerProfileDTO(
                    borrower_id=str(buyer.id),
                    gross_income=gross_income,
                    existing_debt_payments=existing_debt_payments,
                    collateral_value=trade_value,
                    existing_assets=buyer.assets
                )

                term_ticks = mortgage_term
                due_tick = simulation.time + term_ticks

                loan_info = simulation.bank.grant_loan(
                    borrower_id=str(buyer.id),
                    amount=loan_amount,
                    interest_rate=mortgage_rate,
                    due_tick=due_tick,
                    borrower_profile=borrower_profile
                )
                
                if loan_info:
                    loan_id = loan_info["loan_id"]
                    # Fractional Reserve: Loan creates a Deposit.

                    # 1. DISBURSEMENT: Transfer funds from Bank (Reserves) to Buyer (Cash)
                    # This ensures conservation of mass (Bank assets decrease, Buyer assets increase)
                    disbursement_success = simulation.settlement_system.transfer(
                        simulation.bank, buyer, loan_amount, "loan_disbursement", tick=simulation.time
                    )

                    if not disbursement_success:
                         logger.error(f"LOAN_DISBURSEMENT_FAIL | Bank could not transfer {loan_amount} to {buyer.id}. Voiding loan.")
                         simulation.bank.void_loan(loan_id)
                         return

                    # 2. DEPOSIT CLEANUP: Reduce the newly created deposit liability
                    # Because we just 'withdrew' it as cash via the transfer above (conceptually).
                    if hasattr(simulation.bank, "withdraw_for_customer"):
                        withdraw_success = simulation.bank.withdraw_for_customer(buyer.id, loan_amount)
                        if not withdraw_success:
                             logger.error(f"LOAN_WITHDRAW_FAIL | Could not reduce deposit for {buyer.id}. Rolling back.")
                             # Rollback Disbursement
                             simulation.settlement_system.transfer(buyer, simulation.bank, loan_amount, "loan_rollback", tick=simulation.time)
                             simulation.bank.void_loan(loan_id)
                             return

                        unit.mortgage_id = loan_id
                    else:
                        # Fallback if bank interface missing (shouldn't happen)
                        unit.mortgage_id = loan_id
                else:
                    unit.mortgage_id = None
            else:
                unit.mortgage_id = None
                
            # 2. Process Funds Transfer (Buyer -> Seller)
            payment_success = False

            if isinstance(seller, Government):
                # Use collect_tax which uses SettlementSystem internally
                # Pass 'buyer' object, not 'buyer.id'
                tax_result = seller.collect_tax(trade_value, "asset_sale", buyer, simulation.time)
                payment_success = tax_result["success"]
            else:
                payment_success = simulation.settlement_system.transfer(
                    buyer, seller, trade_value, f"purchase_unit_{unit.id}", tick=simulation.time
                )

            if not payment_success:
                 logger.error(f"HOUSING_PAYMENT_FAIL | Buyer {buyer.id} could not pay {trade_value} to Seller {seller.id}. Rolling back.")
                 # Rollback Loan if it existed
                 if loan_id:
                      # 1. Return Cash to Bank (Reverse Disbursement)
                      simulation.settlement_system.transfer(buyer, simulation.bank, loan_amount, "loan_rollback", tick=simulation.time)

                      # 2. Void Loan (Cleanup Loan Asset)
                      try:
                          simulation.bank.void_loan(loan_id)
                      except Exception as e:
                          logger.warning(f"ROLLBACK_WARNING | void_loan failed during rollback: {e}")
                          if loan_id in simulation.bank.loans:
                               del simulation.bank.loans[loan_id]

                 return

            # 3. Transfer Title
            unit.owner_id = buyer.id
            
            # 4. Update Agent Property Lists
            if hasattr(seller, "owned_properties"):
                if unit.id in seller.owned_properties:
                    seller.owned_properties.remove(unit.id)
            
            if hasattr(buyer, "owned_properties"):
                if unit.id not in buyer.owned_properties:
                    buyer.owned_properties.append(unit.id)
                if getattr(buyer, "residing_property_id", None) is None:
                    unit.occupant_id = buyer.id
                    buyer.residing_property_id = unit.id
                    buyer.is_homeless = False
            
            logger.info(
                f"REAL_ESTATE | Sold Unit {unit.id} to {buyer.id}. Price: {trade_value:.2f}",
                extra={"tick": simulation.time, "tags": ["real_estate"]}
            )

        except Exception as e:
            logger.error(f"HOUSING_ERROR | {e}", extra={"error": str(e)})
            raise e
