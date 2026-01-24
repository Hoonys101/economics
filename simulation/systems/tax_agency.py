import logging
from typing import Any

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
        Records revenue statistics WITHOUT attempting collection.
        Used when funds are transferred via SettlementSystem manually.
        """
        if amount <= 0:
            return

        government.total_collected_tax += amount
        government.revenue_this_tick += amount
        # government.total_money_destroyed += amount  <-- REMOVED: Tax is Transfer, not Destruction
        government.tax_revenue[tax_type] = (
            government.tax_revenue.get(tax_type, 0.0) + amount
        )
        government.current_tick_stats["tax_revenue"][tax_type] = (
            government.current_tick_stats["tax_revenue"].get(tax_type, 0.0) + amount
        )
        government.current_tick_stats["total_collected"] += amount

        logger.info(
            f"TAX_RECORDED | Recorded {amount:.2f} as {tax_type} from {payer_id}",
            extra={
                "tick": current_tick,
                "agent_id": government.id,
                "amount": amount,
                "tax_type": tax_type,
                "source_id": payer_id,
                "tags": ["tax", "revenue", "recorded"],
            },
        )

    def collect_tax(self, government, amount: float, tax_type: str, payer: Any, current_tick: int) -> float:
        """
        Executes tax collection via FinanceSystem and records statistics.
        payer: IFinancialEntity (Firm, Household, etc.)
        """
        if amount <= 0:
            return 0.0

        payer_id = payer.id if hasattr(payer, 'id') else payer

        # Delegate to FinanceSystem for atomic transfer
        if hasattr(government, 'finance_system') and government.finance_system:
            if hasattr(payer, 'id'):
                 success = government.finance_system.collect_corporate_tax(payer, amount)
                 if not success:
                      logger.warning(f"TAX_COLLECTION_FAILED | Failed to collect {amount} from {payer_id}")
                      return 0.0
            else:
                 logger.error(f"TAX_COLLECTION_ERROR | Payer {payer} is not an object. Cannot use FinanceSystem.")
                 return 0.0
        else:
            logger.error("TAX_COLLECTION_ERROR | No FinanceSystem linked to Government.")
            return 0.0

        government.total_collected_tax += amount
        government.revenue_this_tick += amount
        # government.total_money_destroyed += amount  <-- REMOVED: Tax is Transfer, not Destruction
        government.tax_revenue[tax_type] = government.tax_revenue.get(tax_type, 0.0) + amount
        government.current_tick_stats["tax_revenue"][tax_type] = government.current_tick_stats["tax_revenue"].get(tax_type, 0.0) + amount
        government.current_tick_stats["total_collected"] += amount

        logger.info(
            f"TAX_COLLECTED | Collected {amount:.2f} as {tax_type} from {payer_id}",
            extra={
                "tick": current_tick,
                "agent_id": government.id,
                "amount": amount,
                "tax_type": tax_type,
                "source_id": payer_id,
                "tags": ["tax", "revenue"]
            }
        )
        return amount
