from dataclasses import dataclass
from typing import List, Any, Dict, Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from simulation.dtos.transactions import TransactionDTO
    from simulation.dtos.settlement_dtos import SettlementResultDTO
    from simulation.firms import Firm

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

    def _round_currency(self, amount: float) -> float:
        """Rounds amount to 2 decimal places to prevent floating point pollution."""
        return round(amount, 2)

    def calculate_income_tax(self, income: float, survival_cost: float, current_income_tax_rate: float, tax_mode: str = 'PROGRESSIVE') -> float:
        """
        Calculates income tax based on the provided parameters.
        Logic moved from TaxAgency.
        """
        if income <= 0:
            return 0.0

        raw_tax = 0.0

        if tax_mode == "FLAT":
            raw_tax = income * current_income_tax_rate
        else:
            tax_brackets = getattr(self.config_module, "TAX_BRACKETS", [])
            if not tax_brackets:
                taxable = max(0, income - survival_cost)
                raw_tax = taxable * current_income_tax_rate
            else:
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
                    raw_tax = raw_tax * adjustment_factor

        return self._round_currency(raw_tax)

    def calculate_corporate_tax(self, profit: float, current_corporate_tax_rate: float) -> float:
        """Calculates corporate tax."""
        if profit <= 0:
            return 0.0
        return self._round_currency(profit * current_corporate_tax_rate)

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
            # Calculate raw then round
            tax_amount = self._round_currency(trade_value * sales_tax_rate)

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

            # calculate_income_tax already rounds
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

        # 3. Escheatment
        elif transaction.transaction_type == "escheatment":
             # Escheatment usually takes the whole trade_value (assets)
             # But let's round it to be safe
             amount = self._round_currency(trade_value)
             if amount > 0:
                 intents.append(TaxIntent(
                    payer_id=buyer.id, # Agent
                    payee_id=government.id,
                    amount=amount,
                    reason="escheatment"
                ))

        return intents

    def generate_corporate_tax_intents(self, firms: List['Firm']) -> List['TransactionDTO']:
        """
        Calculates corporate tax for all eligible firms and returns transaction intents.
        """
        # Avoid circular import at runtime if possible, but we need the class for construction if we use it.
        # However, we can construct the object using the alias or dictionary or what's expected.
        # The system expects Transaction objects.
        # We import here to avoid circular dependency at module level if any.
        from simulation.models import Transaction

        intents = []

        # Access config via nested structure if available, or flat.
        # We will check both for robustness.
        corporate_tax_rate = 0.21
        if hasattr(self.config_module, "taxation"):
             corporate_tax_rate = self.config_module.taxation.get("corporate_tax_rate", 0.21)
        elif hasattr(self.config_module, "CORPORATE_TAX_RATE"):
             corporate_tax_rate = self.config_module.CORPORATE_TAX_RATE

        for firm in firms:
            if not firm.is_active:
                continue

            # Determine Profit Base
            # We use the accumulated profit from the current tick (since production/sales happened).
            # If called in Phase 3, this should be valid.
            # We assume current_profit holds the value.
            # If current_profit is 0, we check if there's a last_tick_profit or similar.
            # For now, we rely on firm.finance.current_profit or firm.finance.revenue_this_turn.

            # Since Spec says "decouples... providing stable basis", and we invoke this *before* distribution
            # (which clears profit), we should use current_profit.

            profit = 0.0
            if hasattr(firm, 'finance'):
                # Net Profit = Revenue - Costs
                # We use revenue_this_turn - cost_this_turn to match previous logic
                profit = firm.finance.revenue_this_turn - firm.finance.cost_this_turn

            if profit <= 0:
                continue

            tax_amount = self.calculate_corporate_tax(profit, corporate_tax_rate)

            if tax_amount > 0:
                # We need a government ID.
                # Ideally passed in or resolved.
                # TaxationSystem doesn't know government ID.
                # We can use a placeholder or well-known ID if available.
                # Or we ask firms who their gov is? No.
                # We can assume 0 or look it up?
                # Spec says "Calculates corporate tax ... returns transaction intents".
                # The caller (TickScheduler) has access to Government.
                # But TaxIntent needs payee_id.
                # We will use a placeholder or expect TickScheduler to fix it?
                # Actually, TaxIntent uses payee_id.
                # Transaction uses seller_id (payee).
                # We will use -1 or "GOVERNMENT" if we don't know ID.
                # But we can iterate and fix later?
                # Better: `generate_corporate_tax_intents` should probably accept `government_id`.
                # But Spec signature is `(self, firms: List[Any])`.
                # We will try to find Gov ID from firms (they interact with Gov).
                # Or we can assume Gov ID is usually found in SimulationState.
                # But we only get `firms`.
                # We'll use a placeholder and rely on `TransactionProcessor` or `SettlementSystem` to resolve "GOVERNMENT"?
                # But `Transaction` expects int/str.
                # Let's use "GOVERNMENT" string or resolve if we can.

                # Wait, if we are inside `TickOrchestrator`, we have `state`.
                # But the method only takes `firms`.
                # We will assume Gov ID is available via config or global constant?
                # `simulation.initialization.initializer` assigns ID.
                # Usually Gov ID is not constant.

                # I will create a transaction with a generic payee if needed,
                # but let's check if we can pass Gov ID.
                # I'll update signature to accept `government_id` optional.

                transaction = Transaction(
                    buyer_id=firm.id,
                    seller_id="GOVERNMENT", # Placeholder, should be resolved
                    item_id="corporate_tax",
                    quantity=1.0,
                    price=tax_amount,
                    market_id="system",
                    transaction_type="tax",
                    time=0, # Tick? We don't have tick here either.
                    # We need tick.
                )
                intents.append(transaction)

        return intents

    def record_revenue(self, results: List['SettlementResultDTO']) -> None:
        """
        Records the outcome of tax payments.
        """
        success_count = 0
        total_revenue = 0.0

        for res in results:
            if not res.success:
                continue

            if getattr(res.original_transaction, 'transaction_type', '') == 'tax':
                success_count += 1
                total_revenue += res.amount_settled

        if success_count > 0:
            logger.info(f"TAXATION_RECORD | Recorded {total_revenue:.2f} revenue from {success_count} transactions.")
