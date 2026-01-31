from dataclasses import dataclass
from typing import List, Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class TaxIntent:
    payer_id: int
    payee_id: int # Usually Government ID
    amount: float
    reason: str

class TaxationSystem:
    """
    Pure logic component for tax calculations.
    Decoupled from Government agent state (policies are passed in) and Settlement execution.
    """
    def __init__(self, config_module: Any):
        self.config_module = config_module

    def calculate_income_tax(self, income: float, survival_cost: float, current_income_tax_rate: float, tax_mode: str = 'PROGRESSIVE') -> float:
        """
        Calculates income tax based on the provided parameters.
        Logic moved from TaxAgency.
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
        """Calculates corporate tax."""
        return profit * current_corporate_tax_rate if profit > 0 else 0.0

    def calculate_tax_intents(
        self,
        transaction: Any, # Transaction model
        buyer: Any,
        seller: Any,
        government: Any,
        market_data: Optional[Dict[str, Any]] = None
    ) -> List[TaxIntent]:
        """
        Determines applicable taxes for a transaction and returns TaxIntents.
        Does NOT execute any transfer.
        """
        intents: List[TaxIntent] = []
        trade_value = transaction.quantity * transaction.price

        # 1. Sales Tax (Goods)
        if transaction.transaction_type == "goods":
            sales_tax_rate = getattr(self.config_module, "SALES_TAX_RATE", 0.05)
            tax_amount = trade_value * sales_tax_rate

            if tax_amount > 0:
                intents.append(TaxIntent(
                    payer_id=buyer.id,
                    payee_id=government.id,
                    amount=tax_amount,
                    reason=f"sales_tax_{transaction.transaction_type}"
                ))

        # 2. Income Tax (Labor)
        elif transaction.transaction_type in ["labor", "research_labor"]:
            # Determine Survival Cost
            avg_food_price = 5.0 # Default
            if market_data:
                goods_market = market_data.get("goods_market", {})
                if "basic_food_current_sell_price" in goods_market:
                    avg_food_price = goods_market["basic_food_current_sell_price"]
                else:
                    # Fallback to config initial price
                    avg_food_price = getattr(self.config_module, "GOODS_INITIAL_PRICE", {}).get("basic_food", 5.0)

            daily_food_need = getattr(self.config_module, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 1.0)
            survival_cost = max(avg_food_price * daily_food_need, 10.0)

            # Get Tax Rate from Government
            # Assuming government object has income_tax_rate attribute
            current_rate = getattr(government, "income_tax_rate", 0.1)
            tax_mode = getattr(self.config_module, "TAX_MODE", "PROGRESSIVE")

            tax_amount = self.calculate_income_tax(trade_value, survival_cost, current_rate, tax_mode)

            if tax_amount > 0:
                tax_payer_type = getattr(self.config_module, "INCOME_TAX_PAYER", "HOUSEHOLD")

                payer_id = buyer.id if tax_payer_type == "FIRM" else seller.id
                reason = "income_tax_firm" if tax_payer_type == "FIRM" else "income_tax_household"

                intents.append(TaxIntent(
                    payer_id=payer_id,
                    payee_id=government.id,
                    amount=tax_amount,
                    reason=reason
                ))

        # 3. Escheatment (If handled here, though it's usually 100% transfer)
        # TransactionProcessor handled 'escheatment' as "collect_tax(trade_value)".
        # This implies it's a transfer to Government.
        # If we handle it here:
        elif transaction.transaction_type == "escheatment":
             intents.append(TaxIntent(
                payer_id=buyer.id, # Agent
                payee_id=government.id,
                amount=trade_value,
                reason="escheatment"
            ))

        return intents
