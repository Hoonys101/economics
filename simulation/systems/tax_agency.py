import logging

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

    def calculate_corporate_tax(self, profit: float, current_corporate_tax_rate: float) -> float:
        """Calculates corporate tax based on the current rate provided by the Government."""
        return profit * current_corporate_tax_rate if profit > 0 else 0.0

    def collect_tax(self, government, amount, tax_type, source_id, current_tick) -> float:
        """
        Records tax collection statistics.
        NOTE: Asset transfer must be handled by SettlementSystem external to this method.
        """
        if amount <= 0:
            return 0.0

        # government.assets += amount  <-- REMOVED: Handled by SettlementSystem
        government.total_collected_tax += amount
        government.revenue_this_tick += amount
        government.total_money_destroyed += amount
        government.tax_revenue[tax_type] = government.tax_revenue.get(tax_type, 0.0) + amount
        government.current_tick_stats["tax_revenue"][tax_type] = government.current_tick_stats["tax_revenue"].get(tax_type, 0.0) + amount
        government.current_tick_stats["total_collected"] += amount

        logger.info(
            f"TAX_COLLECTED | Collected {amount:.2f} as {tax_type} from {source_id}",
            extra={
                "tick": current_tick,
                "agent_id": government.id,
                "amount": amount,
                "tax_type": tax_type,
                "source_id": source_id,
                "tags": ["tax", "revenue"]
            }
        )
        return amount
