from dataclasses import dataclass
from typing import List, Any, Dict, Optional, TYPE_CHECKING, Protocol, Tuple, Union
import logging
from modules.finance.api import IFinancialAgent
from modules.simulation.api import IGovernment
from simulation.models import Transaction
from modules.system.api import DEFAULT_CURRENCY
from modules.finance.utils.currency_math import round_to_pennies
from modules.government.constants import DEFAULT_BASIC_FOOD_PRICE, DEFAULT_HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK
from modules.government.dtos import TaxBracketDTO

if TYPE_CHECKING:
    from simulation.dtos.transactions import TransactionDTO
    from simulation.dtos.settlement_dtos import SettlementResultDTO
    from simulation.firms import Firm

logger = logging.getLogger(__name__)

class ITaxConfig(Protocol):
    TAX_BRACKETS: List[Tuple[float, float]]
    TAX_RATE_BASE: float
    SALES_TAX_RATE: float
    GOODS_INITIAL_PRICE: Dict[str, float]
    HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK: float
    TAX_MODE: str
    INCOME_TAX_PAYER: str
    CORPORATE_TAX_RATE: float

@dataclass
class TaxIntent:
    payer_id: int
    payee_id: int # Usually Government ID
    amount: int
    reason: str

class TaxationSystem:
    """
    Pure logic component for tax calculations.
    Decoupled from Government agent state (policies are passed in) and Settlement execution.
    """
    def __init__(self, config_module: Any): # Keeping Any for broad config, but internally using attributes of ITaxConfig
        self.config_module = config_module

    def _round_currency(self, amount: float) -> int:
        """Rounds amount to integer pennies to prevent floating point pollution."""
        return round_to_pennies(amount)

    def calculate_income_tax(
        self,
        income: int,
        survival_cost: int,
        current_income_tax_rate: float,
        tax_mode: str = 'PROGRESSIVE',
        tax_brackets: Optional[List[TaxBracketDTO]] = None
    ) -> int:
        """
        Calculates income tax based on the provided parameters.
        Logic moved from TaxAgency.
        income and survival_cost are in pennies.
        """
        income_val = income
        if income_val <= 0:
            return 0

        raw_tax = 0.0
        if tax_mode == "FLAT":
            raw_tax = income_val * current_income_tax_rate
            return self._round_currency(raw_tax)

        # NEW LOGIC: Use TaxBracketDTO if provided
        if tax_brackets and len(tax_brackets) > 0:
            # Sort brackets by threshold descending
            # Using absolute thresholds (pennies)
            sorted_brackets = sorted(tax_brackets, key=lambda b: b.threshold, reverse=True)

            current_level_income = income_val

            for bracket in sorted_brackets:
                if current_level_income > bracket.threshold:
                    taxable_amount = current_level_income - bracket.threshold
                    raw_tax += taxable_amount * bracket.rate
                    current_level_income = bracket.threshold

        # LEGACY LOGIC fallback
        else:
            tax_brackets_legacy = getattr(self.config_module, "TAX_BRACKETS", [])
            if not tax_brackets_legacy:
                taxable = max(0.0, income_val - survival_cost)
                raw_tax = taxable * current_income_tax_rate
            else:
                previous_limit_abs = 0.0
                for multiple, rate in tax_brackets_legacy:
                    # Brackets are defined as multiples of survival_cost
                    limit_abs = multiple * survival_cost
                    upper_bound = min(income_val, limit_abs)
                    lower_bound = max(0.0, previous_limit_abs)
                    taxable_amount = max(0.0, upper_bound - lower_bound)

                    if taxable_amount > 0:
                        raw_tax += taxable_amount * rate

                    if income_val <= limit_abs:
                        break
                    previous_limit_abs = limit_abs

                base_rate_config = getattr(self.config_module, "TAX_RATE_BASE", 0.1)
                if base_rate_config > 0:
                    adjustment_factor = current_income_tax_rate / base_rate_config
                    raw_tax = raw_tax * adjustment_factor

        return self._round_currency(raw_tax)

    def calculate_corporate_tax(self, profit: int, current_corporate_tax_rate: float) -> int:
        """Calculates corporate tax."""
        if profit <= 0:
            return 0
        return self._round_currency(profit * current_corporate_tax_rate)

    def calculate_tax_intents(
        self,
        transaction: Transaction,
        buyer: IFinancialAgent,
        seller: IFinancialAgent,
        government: IGovernment,
        market_data: Optional[Dict[str, Any]] = None
    ) -> List[TaxIntent]:
        """
        Determines applicable taxes for a transaction and returns TaxIntents.
        Does NOT execute any transfer.
        """
        intents: List[TaxIntent] = []

        # Use total_pennies for precision if available
        if hasattr(transaction, 'total_pennies') and transaction.total_pennies is not None:
             trade_value = transaction.total_pennies
        else:
             trade_value = int(transaction.quantity * transaction.price)

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
            # MIGRATION: DEFAULT_BASIC_FOOD_PRICE is now pennies (500)
            avg_food_price_pennies = DEFAULT_BASIC_FOOD_PRICE

            if market_data:
                goods_market = market_data.get("goods_market", {})
                if "basic_food_current_sell_price" in goods_market:
                    price_raw = goods_market["basic_food_current_sell_price"]
                    # Assume market data prices are FLOAT DOLLARS.
                    # Convert to pennies safely.
                    avg_food_price_pennies = round_to_pennies(price_raw * 100)
                else:
                    # Fallback to config. Config might be updated to pennies or not?
                    # Since we updated constants.py to pennies, let's check if config overrides it.
                    # Ideally, config should be consistent.
                    # But if config provides dollars (legacy), we might have issues.
                    # However, "hardening the source" implies we assume the system is migrating to pennies.
                    # But wait, `GOODS_INITIAL_PRICE` is likely float dollars in config.json files.
                    # So we should convert it if it looks like dollars?
                    # Or assume we updated Config loading logic?
                    # The safest bet for "Config" values loaded from external JSONs (legacy) is that they are dollars.
                    # BUT `DEFAULT_BASIC_FOOD_PRICE` is pennies now.
                    # I will assume that IF it comes from `goods_market` (live data), it is dollars (float).
                    # IF it comes from Config, I'll convert it assuming it's dollars unless it's huge.
                    # OR, better: always use `round_to_pennies` if it is float.
                    val = getattr(self.config_module, "GOODS_INITIAL_PRICE", {}).get("basic_food", DEFAULT_BASIC_FOOD_PRICE)
                    if isinstance(val, float):
                        avg_food_price_pennies = round_to_pennies(val * 100)
                    else:
                        avg_food_price_pennies = int(val)

            daily_food_need = getattr(self.config_module, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", DEFAULT_HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK)

            # survival_cost in pennies
            # daily_food_need is float quantity.
            survival_cost = int(max(avg_food_price_pennies * daily_food_need, 1000)) # Min 1000 pennies ($10)

            # Get Tax Rate from Government
            # Assuming government object has income_tax_rate attribute
            current_rate = getattr(government, "income_tax_rate", 0.1)
            tax_mode = getattr(self.config_module, "TAX_MODE", "PROGRESSIVE")

            # Fetch tax brackets from Government Fiscal Policy
            # IGovernment doesn't strictly enforce fiscal_policy, but GovernmentAgent has it.
            fiscal_policy = getattr(government, 'fiscal_policy', None)
            tax_brackets = None
            if fiscal_policy and hasattr(fiscal_policy, 'tax_brackets'):
                 tax_brackets = fiscal_policy.tax_brackets

            # calculate_income_tax already rounds
            tax_amount = self.calculate_income_tax(
                income=trade_value,
                survival_cost=survival_cost,
                current_income_tax_rate=current_rate,
                tax_mode=tax_mode,
                tax_brackets=tax_brackets
            )

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

    def generate_corporate_tax_intents(self, firms: List['Firm'], current_tick: int) -> List['TransactionDTO']:
        """
        Calculates corporate tax for all eligible firms and returns transaction intents.
        """
        # Avoid circular import at runtime
        from simulation.models import Transaction

        intents = []

        # Resolve corporate tax rate from config strict (No Fallback)
        if hasattr(self.config_module, "taxation"):
             corporate_tax_rate = self.config_module.taxation.get("corporate_tax_rate")
        elif hasattr(self.config_module, "CORPORATE_TAX_RATE"):
             corporate_tax_rate = self.config_module.CORPORATE_TAX_RATE
        else:
             corporate_tax_rate = None

        if corporate_tax_rate is None:
            raise KeyError("CORPORATE_TAX_RATE not found in config. Cannot calculate corporate tax.")

        for firm in firms:
            if not firm.is_active:
                continue

            # Determine Profit Base (Net Profit = Revenue - Costs)
            profit = 0
            if hasattr(firm, 'finance'):
                rev = firm.finance.revenue_this_turn
                cost = firm.finance.cost_this_turn

                rev_val = int(rev.get(DEFAULT_CURRENCY, 0)) if isinstance(rev, dict) else int(rev)
                cost_val = int(cost.get(DEFAULT_CURRENCY, 0)) if isinstance(cost, dict) else int(cost)

                profit = rev_val - cost_val

            if profit <= 0:
                continue

            tax_amount = self.calculate_corporate_tax(profit, corporate_tax_rate)

            if tax_amount > 0:
                # Convert pennies to dollars for display price
                price_display = tax_amount / 100.0

                transaction = Transaction(
                    buyer_id=firm.id,
                    seller_id="GOVERNMENT", # Placeholder, will be resolved by Orchestrator
                    item_id="corporate_tax",
                    quantity=1.0,
                    price=price_display,
                    market_id="system",
                    transaction_type="tax",
                    time=current_tick
                , total_pennies=tax_amount)
                intents.append(transaction)

        return intents

    def record_revenue(self, results: List['SettlementResultDTO']) -> None:
        """
        Records the outcome of tax payments.
        """
        success_count = 0
        total_revenue = 0

        for res in results:
            if not res.success:
                continue

            if getattr(res.original_transaction, 'transaction_type', '') == 'tax':
                success_count += 1
                total_revenue += int(res.amount_settled)

        if success_count > 0:
            logger.info(f"TAXATION_RECORD | Recorded {total_revenue} revenue from {success_count} transactions.")
