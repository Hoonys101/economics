import logging
from typing import Any
from modules.finance.api import TaxCollectionResult

logger = logging.getLogger(__name__)

class TaxAgency:
    def __init__(self, config_module):
        self.config_module = config_module

    def calculate_income_tax(self, income: float, survival_cost: float, current_income_tax_rate: float, tax_mode: str = 'PROGRESSIVE') -> float:
        """
        Calculates income tax based on the current rate provided by the Government.
        """
        if income <= 0:
            return 0.0

        if tax_mode == "FLAT":
            return income * current_income_tax_rate

        tax_brackets = getattr(self.config_module, "TAX_BRACKETS", [])
        if not tax_brackets:
            taxable = max(0, income - survival_cost)
            return taxable * current_income_tax_rate

        raw_tax = 0.0
        previous_limit_abs = 0.0
        for multiple, rate in tax_brackets:
            limit_abs = multiple * survival_cost
            upper_bound = min(income, limit_abs)
            lower_bound = max(0, previous_limit_abs)
            taxable_amount = max(0.0, upper_bound - lower_bound)

            if taxable_amount > 0:
                raw_tax += taxable_amount * rate

            if income <= limit_abs:
                break
            previous_limit_abs = limit_abs

        base_rate_config = getattr(self.config_module, "TAX_RATE_BASE", 0.1)
        if base_rate_config > 0:
            adjustment_factor = current_income_tax_rate / base_rate_config
            return raw_tax * adjustment_factor

        return raw_tax

    def calculate_corporate_tax(
        self, profit: float, current_corporate_tax_rate: float
    ) -> float:
        """Calculates corporate tax based on the current rate provided by the Government."""
        return profit * current_corporate_tax_rate if profit > 0 else 0.0

    def record_revenue(
        self, government, amount: float, tax_type: str, payer_id: Any, current_tick: int
    ):
        """
        [DEPRECATED] This method is the source of phantom revenue and will be removed.
        All logic is merged into the new atomic collect_tax method in Government.
        """
        logger.warning(
            "DEPRECATED: TaxAgency.record_revenue called. Use atomic collect_tax instead.",
            extra={"tick": current_tick, "tag": "deprecation"}
        )
        pass

    def collect_tax(
        self,
        payer: Any,
        payee: Any,
        amount: float,
        tax_type: str,
        settlement_system: Any,
        current_tick: int
    ) -> TaxCollectionResult:
        """
        [NEW & UNIFIED] Atomically collects tax by executing a transfer and only
        returning a success result if the transfer is confirmed. This method does
        NOT modify any agent's state (other than via settlement).

        Args:
            payer: The entity paying the tax (must have .id and be compatible with ISettlementSystem).
            payee: The entity receiving the tax (must have .id).
            amount: The amount of tax to be collected.
            tax_type: The type of tax (e.g., 'wealth_tax', 'corporate_tax').
            settlement_system: The system responsible for executing the fund transfer.
            current_tick: The current simulation tick.

        Returns:
            A TaxCollectionResult DTO with the outcome of the transaction.
        """
        payer_id = payer.id if hasattr(payer, 'id') else str(payer)
        payee_id = payee.id if hasattr(payee, 'id') else str(payee)

        if amount <= 0:
            return TaxCollectionResult(
                success=True,
                amount_collected=0.0,
                tax_type=tax_type,
                payer_id=payer_id,
                payee_id=payee_id,
                error_message=None
            )

        if not settlement_system:
             logger.error("TAX_COLLECTION_ERROR | No SettlementSystem provided.")
             return TaxCollectionResult(
                success=False,
                amount_collected=0.0,
                tax_type=tax_type,
                payer_id=payer_id,
                payee_id=payee_id,
                error_message="No SettlementSystem provided."
            )

        # 1. Attempt the fund transfer via the injected settlement system.
        transfer_success = settlement_system.transfer(
            debit_agent=payer,
            credit_agent=payee,
            amount=amount,
            memo=f"{tax_type} collection"
        )

        # 2. Verify the outcome.
        if not transfer_success:
            logger.warning(
                f"TAX_COLLECTION_FAILED | Tick {current_tick} | Failed to collect {amount:.2f} of {tax_type} from {payer_id} to {payee_id}",
                extra={"tick": current_tick, "payer_id": payer_id, "amount": amount, "tax_type": tax_type}
            )
            return TaxCollectionResult(
                success=False,
                amount_collected=0.0,
                tax_type=tax_type,
                payer_id=payer_id,
                payee_id=payee_id,
                error_message="Insufficient funds or transfer failed."
            )

        # 3. On success, return a result DTO with the collected amount.
        logger.info(
            f"TAX_COLLECTION_SUCCESS | Tick {current_tick} | Collected {amount:.2f} of {tax_type} from {payer_id}",
            extra={
                "tick": current_tick,
                "agent_id": payee_id,
                "amount": amount,
                "tax_type": tax_type,
                "source_id": payer_id,
                "tags": ["tax", "revenue"]
            }
        )
        return TaxCollectionResult(
            success=True,
            amount_collected=amount,
            tax_type=tax_type,
            payer_id=payer_id,
            payee_id=payee_id,
            error_message=None
        )
