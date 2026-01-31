from typing import List, Any, Dict, Optional, TYPE_CHECKING
from modules.government.taxation.api import ITaxationSystem, TaxIntentDTO
import logging
from collections import defaultdict

if TYPE_CHECKING:
    from simulation.models import Transaction
    from simulation.dtos.api import SimulationState

logger = logging.getLogger(__name__)

class TaxationSystem(ITaxationSystem):
    """
    Pure logic component for tax calculations.
    Decoupled from Government agent state (policies are passed in) and Settlement execution.
    Maintains a ledger of collected tax revenue.
    """
    def __init__(self, config_module: Any):
        self.config_module = config_module
        self.tax_revenue_ledger: Dict[str, float] = {}
        # Stores revenue per tick: {tick: {tax_type: amount}}
        self.revenue_by_tick: Dict[int, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

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

    def generate_tax_intents(
        self,
        transaction: "Transaction",
        state: "SimulationState"
    ) -> List[TaxIntentDTO]:
        """
        Determines applicable taxes for a transaction and returns TaxIntentDTOs.
        Does NOT execute any transfer.
        """
        intents: List[TaxIntentDTO] = []
        trade_value = transaction.quantity * transaction.price

        government = state.government
        if not government:
            logger.error("TaxationSystem: Government not found in state.")
            return []

        buyer = state.agents.get(transaction.buyer_id) or getattr(state, "inactive_agents", {}).get(transaction.buyer_id)
        seller = state.agents.get(transaction.seller_id) or getattr(state, "inactive_agents", {}).get(transaction.seller_id)

        market_data = state.market_data if state.market_data else {}

        # 1. Sales Tax (Goods)
        if transaction.transaction_type == "goods":
            sales_tax_rate = getattr(self.config_module, "SALES_TAX_RATE", 0.05)
            tax_amount = trade_value * sales_tax_rate

            if tax_amount > 0:
                intents.append(TaxIntentDTO(
                    payer_id=transaction.buyer_id,
                    payee_id=government.id,
                    amount=tax_amount,
                    tax_type=f"sales_tax_{transaction.transaction_type}"
                ))

        # 2. Income Tax (Labor)
        elif transaction.transaction_type in ["labor", "research_labor"]:
            if not buyer or not seller:
                 # It's possible for agents to be missing if they were just removed, but transaction remains?
                 # Or if ids are invalid.
                 # logger.warning(f"TaxationSystem: Missing agents for labor tax calc. Buyer: {transaction.buyer_id}, Seller: {transaction.seller_id}")
                 return []

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
            current_rate = getattr(government, "income_tax_rate", 0.1)
            tax_mode = getattr(self.config_module, "TAX_MODE", "PROGRESSIVE")

            tax_amount = self.calculate_income_tax(trade_value, survival_cost, current_rate, tax_mode)

            if tax_amount > 0:
                tax_payer_type = getattr(self.config_module, "INCOME_TAX_PAYER", "HOUSEHOLD")

                payer_id = buyer.id if tax_payer_type == "FIRM" else seller.id
                reason = "income_tax_firm" if tax_payer_type == "FIRM" else "income_tax_household"

                intents.append(TaxIntentDTO(
                    payer_id=payer_id,
                    payee_id=government.id,
                    amount=tax_amount,
                    tax_type=reason
                ))

        # 3. Escheatment
        elif transaction.transaction_type == "escheatment":
             intents.append(TaxIntentDTO(
                payer_id=transaction.buyer_id,
                payee_id=government.id,
                amount=trade_value,
                tax_type="escheatment"
            ))

        return intents

    def record_revenue(self, intent: TaxIntentDTO, success: bool, tick: int) -> None:
        if success:
            tax_type = intent['tax_type']
            amount = intent['amount']
            self.tax_revenue_ledger[tax_type] = self.tax_revenue_ledger.get(tax_type, 0.0) + amount
            self.revenue_by_tick[tick][tax_type] += amount

    def get_tick_revenue(self, tick: int) -> Dict[str, float]:
        """Returns the revenue breakdown for a specific tick."""
        return dict(self.revenue_by_tick.get(tick, {}))
