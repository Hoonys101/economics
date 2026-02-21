from typing import Any, Optional, Tuple, Dict
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from modules.market.api import IHousingTransactionHandler, HousingConfigDTO, IHousingTransactionParticipant, HousingTransactionContextDTO
from modules.finance.api import BorrowerProfileDTO, LienDTO, IFinancialAgent
from modules.system.escrow_agent import EscrowAgent
from modules.common.interfaces import IPropertyOwner
from modules.system.api import DEFAULT_CURRENCY
from simulation.firms import Firm
from modules.simulation.api import AgentID
from modules.finance.utils.currency_math import round_to_pennies

logger = logging.getLogger(__name__)

class HousingTransactionHandler(ITransactionHandler, IHousingTransactionHandler):
    """
    Handles 'housing' market transactions using the Saga pattern.
    Orchestrates atomic settlement involving Buyer, Seller, Bank, and Escrow.
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, state: Any) -> bool:
        """
        Executes the housing transaction saga:
        1. Validation
        2. Down Payment (Buyer -> Escrow)
        3. Mortgage Creation (Bank -> Loan)
        4. Loan Disbursement (Bank -> Escrow)
        5. Final Settlement (Escrow -> Seller)
        """
        # Map state to HousingTransactionContextDTO
        context = self._build_context(state)

        # 1. Initialization & Validation
        if not buyer or not seller:
            logger.error(f"HOUSING | Invalid participants. Buyer: {buyer}, Seller: {seller}")
            return False

        # Find Escrow Agent
        escrow_agent = next((a for a in context.agents.values() if isinstance(a, EscrowAgent)), None)
        if not escrow_agent:
            logger.critical("HOUSING | Escrow Agent not found in simulation agents.")
            return False

        # Parse Unit
        try:
            unit_id = int(tx.item_id.split("_")[1])
            unit = next((u for u in context.real_estate_units if u.id == unit_id), None)
            if not unit:
                logger.error(f"HOUSING | Unit {unit_id} not found.")
                return False
        except (IndexError, ValueError):
            logger.error(f"HOUSING | Invalid item_id format: {tx.item_id}")
            return False

        # Config
        housing_config = getattr(context.config_module, "housing", {})
        # Fallback defaults if config is missing (safety)
        max_ltv = housing_config.get("max_ltv_ratio", 0.8)
        mortgage_term = housing_config.get("mortgage_term_ticks", 300)

        # Interest Rate (Bank Config or Global)
        mortgage_rate = getattr(context.config_module, "MORTGAGE_INTEREST_RATE", 0.05)

        if getattr(tx, 'total_pennies', 0) > 0:
            sale_price = tx.total_pennies
        else:
            # Fallback for legacy transactions without total_pennies
            # Assume price is in dollars
            sale_price = round_to_pennies(tx.price * tx.quantity * 100)
        loan_amount = 0.0
        down_payment = sale_price

        # Determine Mortgage Eligibility
        # Strict Protocol Check
        is_borrower = isinstance(buyer, IHousingTransactionParticipant)
        use_mortgage = is_borrower and context.bank is not None

        if use_mortgage:
            loan_amount = sale_price * max_ltv
            down_payment = sale_price - loan_amount

        # TD-213: Support Multi-Currency Transactions
        tx_currency = getattr(tx, "currency", DEFAULT_CURRENCY)

        # Check Buyer Funds for Down Payment
        buyer_assets = 0.0
        if isinstance(buyer, IFinancialAgent):
             buyer_assets = buyer.get_balance(tx_currency)
        else:
             buyer_assets = 0.0

        if buyer_assets < down_payment:
            logger.info(f"HOUSING | Buyer {buyer.id} insufficient funds for down payment {down_payment:.2f}")
            return False

        # 2. Saga Step A: Secure Down Payment (Buyer -> Escrow)
        memo_down = f"escrow_hold:down_payment:{tx.item_id}"
        if not context.settlement_system.transfer(buyer, escrow_agent, down_payment, memo_down, tick=context.time, currency=tx_currency):
            logger.warning(f"HOUSING | Failed to secure down payment from {buyer.id}")
            return False

        loan_id = None
        new_loan_dto = None

        try:
            # 3. Saga Step B: Create Mortgage (if applicable)
            if use_mortgage:
                borrower_profile = self._create_borrower_profile(buyer, sale_price, context, currency=tx_currency)
                due_tick = context.time + mortgage_term

                grant_result = context.bank.grant_loan(
                    borrower_id=buyer.id,
                    amount=loan_amount,
                    interest_rate=mortgage_rate,
                    due_tick=due_tick,
                    borrower_profile=borrower_profile
                )

                if not grant_result:
                    logger.warning(f"HOUSING | Bank rejected mortgage for {buyer.id}")
                    # Compensate Step A
                    context.settlement_system.transfer(escrow_agent, buyer, down_payment, "escrow_reversal:loan_rejected", tick=context.time, currency=tx_currency)
                    return False

                new_loan_dto, credit_tx = grant_result
                loan_id = new_loan_dto['loan_id']

                # Append credit creation tx to queue if provided
                if credit_tx and context.transaction_queue is not None:
                    context.transaction_queue.append(credit_tx)

                # 4. Saga Step C: Disburse Loan (Bank -> Escrow)
                # Correction: funds must originate from BANK.
                # But `grant_loan` already created a deposit for Buyer. We must withdraw it first.
                try:
                    # Neutralize the deposit created by grant_loan
                    withdrawal_success = context.bank.withdraw_for_customer(buyer.id, loan_amount)
                    if not withdrawal_success:
                        logger.critical(f"HOUSING | Failed to withdraw loan deposit from Buyer {buyer.id}. Aborting.")
                        self._void_loan_safely(context, loan_id)
                        context.settlement_system.transfer(escrow_agent, buyer, down_payment, "escrow_reversal:disbursement_failed", tick=context.time, currency=tx_currency)
                        return False
                except Exception as e:
                    logger.critical(f"HOUSING | Error withdrawing loan deposit: {e}")
                    self._void_loan_safely(context, loan_id)
                    context.settlement_system.transfer(escrow_agent, buyer, down_payment, "escrow_reversal:disbursement_failed", tick=context.time, currency=tx_currency)
                    return False

                memo_disburse = f"escrow_hold:loan_proceeds:{tx.item_id}"
                # Transfer from BANK (Reserves) to Escrow
                if not context.settlement_system.transfer(context.bank, escrow_agent, loan_amount, memo_disburse, tick=context.time, currency=tx_currency):
                    logger.critical(f"HOUSING | Failed to move loan proceeds from Bank to Escrow for {buyer.id}")
                    # Compensate: Terminate Loan (Asset), Return Down Payment
                    self._terminate_loan_safely(context, loan_id)
                    context.settlement_system.transfer(escrow_agent, buyer, down_payment, "escrow_reversal:disbursement_failed", tick=context.time, currency=tx_currency)
                    return False

            # 5. Saga Step D: Final Settlement (Escrow -> Seller)
            memo_settle = f"final_settlement:{tx.item_id}"

            if not context.settlement_system.transfer(escrow_agent, seller, sale_price, memo_settle, tick=context.time, currency=tx_currency):
                logger.critical(f"HOUSING | CRITICAL: Failed to pay seller {seller.id} from escrow.")
                # Compensate:
                # 1. Return Loan Proceeds to BANK
                if use_mortgage:
                    context.settlement_system.transfer(escrow_agent, context.bank, loan_amount, "reversal:loan_return_to_bank", tick=context.time, currency=tx_currency)
                    self._terminate_loan_safely(context, loan_id)

                # 2. Return Down Payment to Buyer
                context.settlement_system.transfer(escrow_agent, buyer, down_payment, "reversal:down_payment_return", tick=context.time, currency=tx_currency)
                return False

            # Success!
            # 6. Apply Side Effects
            lender_id = context.bank.id if context.bank else 0
            self._apply_housing_effects(unit, buyer, seller, loan_id, loan_amount, lender_id, context)

            if loan_id:
                if not tx.metadata: tx.metadata = {}
                tx.metadata["mortgage_id"] = loan_id
                tx.metadata["loan_principal"] = loan_amount
                tx.metadata["lender_id"] = lender_id

            logger.info(f"HOUSING | Success: Unit {unit.id} sold to {buyer.id}. Price: {sale_price}")
            return True

        except Exception as e:
            logger.error(f"HOUSING | Unexpected error: {e}", exc_info=True)
            return False

    def _build_context(self, state: Any) -> HousingTransactionContextDTO:
        """Adapts SimulationState or TransactionContext to DTO."""
        return HousingTransactionContextDTO(
            settlement_system=state.settlement_system,
            bank=getattr(state, 'bank', None),
            government=getattr(state, 'government', None),
            real_estate_units=getattr(state, 'real_estate_units', []),
            agents=getattr(state, 'agents', {}),
            config_module=getattr(state, 'config_module', None),
            time=getattr(state, 'time', 0),
            transaction_queue=getattr(state, 'transaction_queue', [])
        )

    def _create_borrower_profile(self, buyer: Any, trade_value: float, context: HousingTransactionContextDTO, currency: str = DEFAULT_CURRENCY) -> BorrowerProfileDTO:
        gross_income = 0.0
        if isinstance(buyer, IHousingTransactionParticipant):
             work_hours = getattr(context.config_module, "WORK_HOURS_PER_DAY", 8.0)
             ticks_per_year = getattr(context.config_module, "TICKS_PER_YEAR", 100.0)
             ticks_per_month = ticks_per_year / 12.0
             gross_income = buyer.current_wage * work_hours * ticks_per_month

        existing_debt = 0.0
        if context.bank:
             try:
                 status = context.bank.get_debt_status(buyer.id)
                 existing_debt = status.total_outstanding_pennies / 100.0
             except: pass

        assets_val = 0.0
        if isinstance(buyer, IFinancialAgent):
             assets_val = buyer.get_balance(currency)

        return BorrowerProfileDTO(
            borrower_id=buyer.id,
            gross_income=gross_income,
            existing_debt_payments=existing_debt * 0.01,
            collateral_value=trade_value
        )

    def _void_loan_safely(self, context: HousingTransactionContextDTO, loan_id: str):
        if context.bank and loan_id:
            try:
                void_tx = context.bank.void_loan(loan_id)
                if void_tx and context.transaction_queue is not None:
                    context.transaction_queue.append(void_tx)
            except Exception as e:
                logger.error(f"HOUSING | Failed to void loan {loan_id}: {e}")

    def _terminate_loan_safely(self, context: HousingTransactionContextDTO, loan_id: str):
        if context.bank and loan_id:
            try:
                term_tx = context.bank.terminate_loan(loan_id)
                if term_tx and context.transaction_queue is not None:
                    context.transaction_queue.append(term_tx)
            except Exception as e:
                logger.error(f"HOUSING | Failed to terminate loan {loan_id}: {e}")

    def _apply_housing_effects(self, unit: Any, buyer: Any, seller: Any, mortgage_id: Optional[str],
                             loan_amount: float, lender_id: int, context: HousingTransactionContextDTO):
        unit_id = unit.id
        unit.owner_id = buyer.id
        unit.liens = [lien for lien in unit.liens if lien['lien_type'] != 'MORTGAGE']

        if mortgage_id:
             new_lien: LienDTO = {
                 "loan_id": str(mortgage_id),
                 "lienholder_id": lender_id,
                 "principal_remaining": loan_amount,
                 "lien_type": "MORTGAGE"
             }
             unit.liens.append(new_lien)

        if seller and isinstance(seller, IPropertyOwner):
             seller.remove_property(unit_id)

        if isinstance(buyer, IPropertyOwner):
            buyer.add_property(unit_id)

            if isinstance(buyer, IHousingTransactionParticipant):
                if buyer.residing_property_id is None:
                    unit.occupant_id = buyer.id
                    buyer.residing_property_id = unit_id
                    buyer.is_homeless = False
