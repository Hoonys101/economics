import logging
from typing import Any, List, Optional, Dict, TYPE_CHECKING
import numpy as np

from modules.finance.api import (
    InsufficientFundsError, IFinancialAgent, IFinancialEntity,
    IBank, ICentralBank, OMOInstructionDTO
)
from modules.finance.wallet.wallet import Wallet
from modules.finance.wallet.api import IWallet
from modules.system.api import ICurrencyHolder, CurrencyCode, DEFAULT_CURRENCY
from modules.system.constants import ID_CENTRAL_BANK
from simulation.models import Order, Transaction

# Wave 5: Strategy Pattern
from modules.finance.monetary.api import (
    IMonetaryStrategy, MonetaryRuleType, MacroEconomicSnapshotDTO,
    MonetaryPolicyConfigDTO, MonetaryDecisionDTO, OMOActionType
)
from modules.finance.monetary.strategies import TaylorRuleStrategy

if TYPE_CHECKING:
    from modules.memory.api import MemoryV2Interface
    from simulation.dtos.strategy import ScenarioStrategy
    from simulation.core_markets import Market

logger = logging.getLogger(__name__)

class CentralBank(ICurrencyHolder, IFinancialAgent, IFinancialEntity, ICentralBank):
    """
    Wave 5: Central Bank Agent.
    Implements Multi-Rule Strategy Pattern for monetary policy.
    Supports Taylor Rule, Friedman k%, and McCallum Rule.
    """

    def __init__(self, tracker: Any, config_module: Any, memory_interface: Optional["MemoryV2Interface"] = None, strategy: Optional["ScenarioStrategy"] = None):
        self.id = ID_CENTRAL_BANK # Identifier for SettlementSystem (TD-220)
        self.tracker = tracker
        self.config_module = config_module
        self.memory_v2 = memory_interface
        self.strategy = strategy # Scenario Strategy (God Mode Override)

        # Balance Sheet
        self.bonds: List[Any] = []
        self.wallet = Wallet(self.id, allow_negative_balance=True)
        self.bond_market: Optional["Market"] = None

        # Initial Rate
        self.base_rate = getattr(config_module, "INITIAL_BASE_ANNUAL_RATE", 0.05)
        if self.strategy and self.strategy.initial_base_interest_rate is not None:
            self.base_rate = self.strategy.initial_base_interest_rate

        # Configuration
        self.update_interval = getattr(config_module, "CB_UPDATE_INTERVAL", 10)
        self.inflation_target = getattr(config_module, "CB_INFLATION_TARGET", 0.02)

        # Initialize Monetary Policy (Internal Brain)
        # Default to Taylor Rule
        self.monetary_policy: IMonetaryStrategy = TaylorRuleStrategy()

        # Initialize Policy Config
        self.monetary_config = MonetaryPolicyConfigDTO(
            rule_type=MonetaryRuleType.TAYLOR_RULE,
            inflation_target=self.inflation_target,
            unemployment_target=getattr(config_module, "CB_UNEMPLOYMENT_TARGET", 0.05),
            m2_growth_target=getattr(config_module, "CB_M2_GROWTH_TARGET", 0.03),
            ngdp_target_growth=getattr(config_module, "CB_NGDP_TARGET_GROWTH", 0.04),
            taylor_alpha=getattr(config_module, "CB_TAYLOR_ALPHA", 1.5),
            taylor_beta=getattr(config_module, "CB_TAYLOR_BETA", 0.5),
            neutral_rate=getattr(config_module, "CB_NEUTRAL_RATE", 0.02)
        )

        # GDP Potential Tracking (EMA) - Retained for internal potential calculation
        self.potential_gdp = 0.0
        self.gdp_ema_alpha = 0.05 # Smoothing factor for Potential GDP (slow moving)

        logger.info(
            f"CENTRAL_BANK_INIT | Rate: {self.base_rate:.2%}, Target Infl: {self.inflation_target:.2%}, Policy: {self.monetary_policy.rule_type}",
            extra={"tick": 0, "tags": ["central_bank", "init"]}
        )

    def set_bond_market(self, market: "Market") -> None:
        """Sets the bond market reference for OMO execution."""
        self.bond_market = market

    @property
    def assets(self) -> Dict[CurrencyCode, int]:
        """Legacy compatibility accessor."""
        return self.wallet.get_all_balances()

    @property
    def balance_pennies(self) -> int:
        return self.wallet.get_balance(DEFAULT_CURRENCY)

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self.wallet.get_balance(currency)

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        return self.wallet.get_all_balances()

    def get_assets_by_currency(self) -> Dict[CurrencyCode, int]:
        """Implementation of ICurrencyHolder."""
        return self.wallet.get_all_balances()

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.wallet.add(amount, currency, memo="Deposit")

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.wallet.subtract(amount, currency, memo="Withdraw")

    def purchase_bonds(self, bond: Any) -> None:
        """
        Purchases government bonds, adding them to the Central Bank's balance sheet.
        This is a key part of Quantitative Easing (QE).
        """
        self.add_bond_to_portfolio(bond)

    def add_bond_to_portfolio(self, bond: Any) -> None:
        """
        Adds a bond to the portfolio.
        Protocol method expected by FinanceSystem.
        """
        self.bonds.append(bond)
        logger.info(
            f"CENTRAL_BANK_QE | Purchased bond {bond.id} for {bond.face_value:.2f}. "
            f"Total bonds held: {len(self.bonds)}",
            extra={"tags": ["central_bank", "qe"]}
        )

    def get_base_rate(self) -> float:
        return self.base_rate

    def step(self, current_tick: int):
        """
        Called every tick by Engine.
        Updates Potential GDP estimate and recalculates rate/executes OMO periodically.
        """
        # 1. Update Potential GDP Estimate (Every tick to be smooth)
        latest_indicators = self.tracker.get_latest_indicators()
        current_gdp = latest_indicators.get("total_production", 0.0) # Quantity or Nominal? Tracker seems to store Quantity as total_production?
        # Wait, EconomicTracker.track: record["total_production"] = sum(f.current_production). This is quantity.
        # record["gdp"] = nominal_gdp = production * price.
        # Potential GDP usually refers to Real GDP (Quantity).
        # So using total_production is correct for Potential Output tracking.

        if current_gdp > 0:
            if self.potential_gdp == 0.0:
                self.potential_gdp = current_gdp
            else:
                self.potential_gdp = (self.gdp_ema_alpha * current_gdp) + ((1 - self.gdp_ema_alpha) * self.potential_gdp)

        # 2. Check Update Interval (and if AI is not in control)
        is_ai_controlled = getattr(self.config_module, "GOVERNMENT_POLICY_MODE", "TAYLOR_RULE") == "AI_ADAPTIVE"

        # WO-147: Check if monetary stabilizer is enabled (default True)
        is_stabilizer_enabled = getattr(self.config_module, "ENABLE_MONETARY_STABILIZER", True)

        if is_stabilizer_enabled and not is_ai_controlled and current_tick > 0 and current_tick % self.update_interval == 0:
            self._execute_monetary_policy(current_tick, latest_indicators)

    def _execute_monetary_policy(self, current_tick: int, indicators: Dict[str, Any]):
        """
        Executes the active monetary strategy.
        """
        # A. Build Snapshot
        snapshot = self._build_snapshot(current_tick, indicators)

        # B. Calculate Decision
        decision = self.monetary_policy.calculate_decision(snapshot, self.base_rate, self.monetary_config)

        # C. Apply Rate Decision
        old_rate = self.base_rate

        # Check for Scenario Override
        if self.strategy and self.strategy.is_active:
             if self.strategy.monetary_shock_target_rate is not None:
                 decision = MonetaryDecisionDTO(
                     rule_type=decision.rule_type,
                     tick=decision.tick,
                     target_interest_rate=self.strategy.monetary_shock_target_rate,
                     omo_action=decision.omo_action,
                     omo_amount_pennies=decision.omo_amount_pennies,
                     reasoning="Scenario Override"
                 )
             if self.strategy.base_interest_rate_multiplier is not None:
                 decision = MonetaryDecisionDTO(
                     rule_type=decision.rule_type,
                     tick=decision.tick,
                     target_interest_rate=decision.target_interest_rate * self.strategy.base_interest_rate_multiplier,
                     omo_action=decision.omo_action,
                     omo_amount_pennies=decision.omo_amount_pennies,
                     reasoning="Scenario Multiplier"
                 )

        self.base_rate = decision.target_interest_rate

        # D. Execute OMO if needed
        if decision.omo_action != OMOActionType.NONE:
            instruction = OMOInstructionDTO(
                operation_type='purchase' if decision.omo_action == OMOActionType.BUY_BONDS else 'sale',
                target_amount=decision.omo_amount_pennies
            )
            orders = self.execute_open_market_operation(instruction)
            # Since self.execute_open_market_operation just creates orders but doesn't place them in current logic?
            # Wait, execute_open_market_operation should PLACE orders if it has bond_market.
            # But the protocol signature returns List[Order].
            # So I should place them here if returned.
            if self.bond_market:
                for order in orders:
                    self.bond_market.place_order(order, current_tick)
                    logger.info(f"CENTRAL_BANK_OMO | Placed order: {order.side} {order.quantity} on {order.market_id}")

        # Logging
        logger.info(
            f"CB_POLICY_EXEC | Rule: {decision.rule_type.name} | Rate: {old_rate:.2%} -> {self.base_rate:.2%} | "
            f"OMO: {decision.omo_action.name} ({decision.omo_amount_pennies}) | Reason: {decision.reasoning}",
            extra={
                "tick": current_tick,
                "old_rate": old_rate,
                "new_rate": self.base_rate,
                "rule": decision.rule_type.name,
                "tags": ["central_bank", "policy"]
            }
        )

    def _build_snapshot(self, tick: int, indicators: Dict[str, Any]) -> MacroEconomicSnapshotDTO:
        # Calculate annual inflation
        price_history = self.tracker.metrics.get("goods_price_index", []) # Used to use avg_goods_price, updated tracker uses goods_price_index
        if not price_history:
             price_history = self.tracker.metrics.get("avg_goods_price", []) # Fallback

        inflation_rate = 0.0
        if len(price_history) > self.update_interval:
            p_current = price_history[-1]
            p_prev = price_history[-self.update_interval]
            if p_prev > 0:
                ticks_per_year = getattr(self.config_module, "TICKS_PER_YEAR", 100)
                period_inflation = (p_current - p_prev) / p_prev
                inflation_rate = period_inflation * (ticks_per_year / self.update_interval)

        # Output Gap
        # Current GDP (Nominal or Real?)
        # Tracker 'gdp' is Nominal. 'total_production' is Real (Quantity).
        current_real_gdp = indicators.get("total_production", 0.0)
        output_gap = 0.0
        if self.potential_gdp > 0:
            output_gap = (current_real_gdp - self.potential_gdp) / self.potential_gdp

        # Real GDP Growth
        # Need history of Real GDP.
        # Using self.potential_gdp as a proxy for trend? No.
        # We can approximate current growth using change in total_production.
        # But for V1, let's assume 0.0 if not tracked, or use change from last tick?
        # Tracker does not give history easily via get_latest_indicators.
        # But we can access self.tracker.metrics["total_production"] if accessible.
        # self.tracker is the instance.
        real_gdp_growth = 0.0
        # If we could access history, we would.

        return MacroEconomicSnapshotDTO(
            tick=tick,
            inflation_rate_annual=inflation_rate,
            nominal_gdp=int(indicators.get("gdp", 0)),
            real_gdp_growth=real_gdp_growth, # Placeholder
            unemployment_rate=indicators.get("unemployment_rate", 0.0) / 100.0, # Tracker stores as percentage 0-100
            current_m2_supply=int(indicators.get("money_supply", 0)), # Pennies
            current_monetary_base=int(indicators.get("monetary_base", 0)), # Pennies (Requires Tracker Update)
            velocity_of_money=indicators.get("velocity_of_money", 0.0),
            output_gap=output_gap
        )

    def _internal_add_assets(self, amount: int) -> None:
        """[INTERNAL ONLY] Increase cash reserves."""
        self.wallet.add(amount, memo="Internal Add")

    def _internal_sub_assets(self, amount: int) -> None:
        """[INTERNAL ONLY] Decrease cash reserves."""
        # Central Bank can withdraw (create money) even if it results in negative cash
        # This represents expansion of the monetary base.
        self.wallet.subtract(amount, memo="Internal Sub")

    def deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deposits a given amount into the central bank's cash reserves."""
        if isinstance(amount, float):
            raise TypeError(f"CentralBank.deposit requires integer amount (pennies). Got float: {amount}")
        if amount > 0:
            self.wallet.add(amount, currency, memo="Deposit")

    def mint(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        Mints new currency (adds to cash reserves).
        Alias for deposit but semantically distinct for Genesis Protocol.
        """
        if isinstance(amount, float):
            raise TypeError(f"CentralBank.mint requires integer amount (pennies). Got float: {amount}")
        self.deposit(amount, currency)

    def withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        Withdraws a given amount from the central bank's cash reserves.
        As a Fiat Currency Issuer, the Central Bank can have a negative balance (creating money).
        """
        if isinstance(amount, float):
            raise TypeError(f"CentralBank.withdraw requires integer amount (pennies). Got float: {amount}")
        if amount > 0:
            self.wallet.subtract(amount, currency, memo="Withdraw")

    # --- IFinancialAgent Implementation ---
    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self.wallet.get_balance(currency)

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        return self.wallet.get_all_balances()

    @property
    def total_wealth(self) -> int:
        return sum(self.wallet.get_all_balances().values())

    def get_liquid_assets(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self.get_balance(currency)

    def get_total_debt(self) -> int:
        return 0

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.wallet.add(amount, currency, memo="Protocol Deposit")

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        # Central Bank can always withdraw (create money)
        self.wallet.subtract(amount, currency, memo="Protocol Withdraw")

    def execute_open_market_operation(self, instruction: OMOInstructionDTO) -> List[Order]:
        """
        Takes an instruction and creates market orders to fulfill it.
        This generates the Orders, but they must be placed by the caller (step method).
        """
        if instruction.target_amount <= 0:
            return []

        orders = []
        # Target Bond ID? Usually "GOV_BOND_10Y" or generic.
        # BondMarket usually matches based on item_id.
        # We assume standard bond ID "gov_bond" or similar.
        # Needs to match what Treasury issues.
        # Treasury uses `issue_treasury_bonds`.
        bond_item_id = "gov_bond_10y" # Assumption, needs verification with FinanceSystem

        if instruction.operation_type == 'purchase':
            # QE: Buy Bonds
            # We need to determine quantity based on target amount (pennies) and market price.
            current_price = 1000.0 # Default fallback (Dollars)
            if self.bond_market:
                market_price = self.bond_market.get_daily_avg_price()
                if market_price and market_price > 0:
                    current_price = market_price

            # Convert price to pennies for calculation
            current_price_pennies = int(current_price * 100)

            # Avoid division by zero
            if current_price_pennies <= 0:
                current_price_pennies = 100000 # Default to $1000

            qty = int(instruction.target_amount / current_price_pennies)
            bid_price = int(current_price_pennies * 1.05) # 5% Premium to ensure fill (Pennies)

            if qty > 0:
                orders.append(Order(
                    agent_id=self.id,
                    item_id=bond_item_id,
                    price_pennies=bid_price,
                    quantity=qty,
                    market_id="security_market",
                    side="BUY"
                ))

        elif instruction.operation_type == 'sale':
            # QT: Sell Bonds
            # Must have bonds to sell
            if not self.bonds:
                logger.warning("CENTRAL_BANK_QT | Force Majeure: Cannot sell bonds (Portfolio Empty).")
                return []

            # Simplified: Sell first available bonds
            # Value to drain = target_amount
            remaining_drain = instruction.target_amount

            # Sort bonds? or LIFO?
            # Just take first.
            if self.bond_market:
                current_price = self.bond_market.get_daily_avg_price() or 1000.0
                current_price_pennies = int(current_price * 100)
                if current_price_pennies <= 0:
                    current_price_pennies = 100000

                qty_needed = int(remaining_drain / current_price_pennies)

                # Check portfolio holdings
                # self.bonds is List[Any] (Bond objects).
                # We need to sell them.
                # This implies placing Sell Orders.
                # Assuming bonds are fungible for "gov_bond_10y" market.

                # We will place one large sell order if we have enough units.
                total_units_held = len(self.bonds) # Assuming 1 unit per object

                qty_to_sell = min(qty_needed, total_units_held)

                if qty_to_sell > 0:
                    orders.append(Order(
                        agent_id=self.id,
                        item_id=bond_item_id,
                        price_pennies=int(current_price_pennies * 0.95), # 5% Discount
                        quantity=qty_to_sell,
                        market_id="security_market",
                        side="SELL"
                    ))

        return orders

    def process_omo_settlement(self, transaction: Transaction) -> None:
        """
        Callback for OMO settlement.
        """
        logger.info(f"CENTRAL_BANK | OMO Settlement processed: {transaction.transaction_id}")
        # If we bought bonds, we need to add them to portfolio?
        # Simulation usually handles asset transfer via TransactionProcessor -> AssetTransferHandler.
        # If handler calls `add_bond_to_portfolio`, we are good.
