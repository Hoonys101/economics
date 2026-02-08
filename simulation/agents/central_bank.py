import logging
from typing import Any, List, Optional, Dict, TYPE_CHECKING
import numpy as np
from modules.finance.api import InsufficientFundsError
from modules.finance.wallet.wallet import Wallet
from modules.finance.wallet.api import IWallet
from modules.system.api import ICurrencyHolder, CurrencyCode, DEFAULT_CURRENCY
from modules.system.constants import ID_CENTRAL_BANK

if TYPE_CHECKING:
    from modules.memory.api import MemoryV2Interface
    from simulation.dtos.strategy import ScenarioStrategy

logger = logging.getLogger(__name__)

class CentralBank(ICurrencyHolder):
    """
    Phase 10: Central Bank Agent.
    Implements Taylor Rule to dynamically adjust interest rates.
    """

    def __init__(self, tracker: Any, config_module: Any, memory_interface: Optional["MemoryV2Interface"] = None, strategy: Optional["ScenarioStrategy"] = None):
        self.id = ID_CENTRAL_BANK # Identifier for SettlementSystem (TD-220)
        self.tracker = tracker
        self.config_module = config_module
        self.memory_v2 = memory_interface
        self.strategy = strategy

        # Balance Sheet
        self.bonds: List[Any] = []
        self.wallet = Wallet(self.id, allow_negative_balance=True)

        # Initial Rate
        self.base_rate = getattr(config_module, "INITIAL_BASE_ANNUAL_RATE", 0.05)
        # WO-136: Check Strategy for Initial Rate
        if self.strategy and self.strategy.initial_base_interest_rate is not None:
            self.base_rate = self.strategy.initial_base_interest_rate

        # Configuration
        self.update_interval = getattr(config_module, "CB_UPDATE_INTERVAL", 10)
        self.inflation_target = getattr(config_module, "CB_INFLATION_TARGET", 0.02)
        self.alpha = getattr(config_module, "CB_TAYLOR_ALPHA", 1.5)
        self.beta = getattr(config_module, "CB_TAYLOR_BETA", 0.5)

        # GDP Potential Tracking (EMA)
        self.potential_gdp = 0.0
        self.gdp_ema_alpha = 0.05 # Smoothing factor for Potential GDP (slow moving)

        logger.info(
            f"CENTRAL_BANK_INIT | Rate: {self.base_rate:.2%}, Target Infl: {self.inflation_target:.2%}",
            extra={"tick": 0, "tags": ["central_bank", "init"]}
        )

    @property
    def assets(self) -> Dict[CurrencyCode, float]:
        """Legacy compatibility accessor."""
        return self.wallet.get_all_balances()

    def get_assets_by_currency(self) -> Dict[CurrencyCode, float]:
        """Implementation of ICurrencyHolder."""
        return self.wallet.get_all_balances()

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
        Updates Potential GDP estimate and recalculates rate periodically.
        """
        # 1. Update Potential GDP Estimate (Every tick to be smooth)
        latest_indicators = self.tracker.get_latest_indicators()
        current_gdp = latest_indicators.get("total_production", 0.0)

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
            self.calculate_rate(current_tick, current_gdp)

    def calculate_rate(self, current_tick: int, current_gdp: float):
        """
        Implements Taylor Rule:
        i_t = r* + pi_t + alpha * (pi_t - pi*) + beta * y_t

        Where:
        - r*: Real neutral rate (assumed 2% or 0.02)
        - pi_t: Current inflation rate
        - pi*: Inflation target
        - y_t: Output gap ((GDP - Potential) / Potential)
        """
        # A. Calculate Inflation
        # We need inflation rate. Tracker usually has 'avg_goods_price'.
        # Calculate % change from history.
        price_history = self.tracker.metrics.get("avg_goods_price", [])

        # Use simple period-over-period inflation (since last update)
        # Check price 'update_interval' ticks ago.
        inflation_rate = 0.0
        if len(price_history) > self.update_interval:
            p_current = price_history[-1]
            p_prev = price_history[-self.update_interval]
            if p_prev > 0:
                # Annualize it?
                # Taylor rule usually uses annual inflation.
                # If interval is 10 ticks and year is 100 ticks, this is 0.1 year.
                # inflation_period = (p_current - p_prev) / p_prev
                # inflation_annual = inflation_period * (TICKS_PER_YEAR / update_interval)
                # Let's keep it simple: just period change for now, or annualize.
                # Standard Taylor Rule uses annual rates.

                ticks_per_year = getattr(self.config_module, "TICKS_PER_YEAR", 100)
                period_inflation = (p_current - p_prev) / p_prev
                inflation_rate = period_inflation * (ticks_per_year / self.update_interval)

        # B. Calculate Output Gap
        output_gap = 0.0
        if self.potential_gdp > 0:
            output_gap = (current_gdp - self.potential_gdp) / self.potential_gdp

        # C. Taylor Rule
        # Assumed Neutral Real Rate (r*) = 0.02 (2%)
        neutral_rate = 0.02

        # Taylor Rule Formula
        # i = r* + pi + alpha(pi - pi*) + beta(y)
        # Wait, standard formula: i = pi + r* + alpha(pi - pi*) + beta(y)
        # Rearranged: i = r* + pi(1 + alpha) - alpha*pi* + beta*y
        # Using alpha=0.5 (standard) means 1.5 response to inflation.
        # My config has ALPHA=1.5. I should assume config ALPHA is the coefficient for (pi - pi*).
        # Formula: i = neutral_rate + inflation_rate + alpha * (inflation_rate - target) + beta * output_gap

        taylor_rate = neutral_rate + inflation_rate + \
                      self.alpha * (inflation_rate - self.inflation_target) + \
                      self.beta * output_gap

        # D. Apply Strategy Overrides (WO-136)
        if self.strategy and self.strategy.is_active:
             # Scenario 4: Fixed Target Rate
             if self.strategy.monetary_shock_target_rate is not None:
                 taylor_rate = self.strategy.monetary_shock_target_rate

             # Multiplier
             if self.strategy.base_interest_rate_multiplier is not None:
                 taylor_rate *= self.strategy.base_interest_rate_multiplier

        # E. Zero Lower Bound (ZLB) and Smoothing
        # ZLB
        target_rate = max(0.0, taylor_rate)

        # Smoothing (Limit max change to 0.25% per update)
        max_change = 0.0025
        delta = target_rate - self.base_rate
        if abs(delta) > max_change:
            target_rate = self.base_rate + (max_change * (1 if delta > 0 else -1))

        old_rate = self.base_rate
        self.base_rate = target_rate

        old_rate_val = old_rate if isinstance(old_rate, (int, float)) else 0.0
        new_rate_val = self.base_rate if isinstance(self.base_rate, (int, float)) else 0.0
        infl_val = inflation_rate if isinstance(inflation_rate, (int, float)) else 0.0
        gap_val = output_gap if isinstance(output_gap, (int, float)) else 0.0
        pot_gdp_val = self.potential_gdp if isinstance(self.potential_gdp, (int, float)) else 0.0

        logger.info(
            f"CB_RATE_UPDATE | Rate: {old_rate_val:.2%} -> {new_rate_val:.2%} "
            f"(Infl: {infl_val:.2%}, Gap: {gap_val:.2%}, PotGDP: {pot_gdp_val:.2f})",
            extra={
                "tick": current_tick,
                "old_rate": old_rate,
                "new_rate": self.base_rate,
                "inflation": inflation_rate,
                "output_gap": output_gap,
                "tags": ["central_bank", "policy"]
            }
        )

    def _internal_add_assets(self, amount: float) -> None:
        """[INTERNAL ONLY] Increase cash reserves."""
        self.wallet.add(amount, memo="Internal Add")

    def _internal_sub_assets(self, amount: float) -> None:
        """[INTERNAL ONLY] Decrease cash reserves."""
        # Central Bank can withdraw (create money) even if it results in negative cash
        # This represents expansion of the monetary base.
        self.wallet.subtract(amount, memo="Internal Sub")

    def deposit(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deposits a given amount into the central bank's cash reserves."""
        if amount > 0:
            self.wallet.add(amount, currency, memo="Deposit")

    def mint(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        Mints new currency (adds to cash reserves).
        Alias for deposit but semantically distinct for Genesis Protocol.
        """
        self.deposit(amount, currency)

    def withdraw(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        Withdraws a given amount from the central bank's cash reserves.
        As a Fiat Currency Issuer, the Central Bank can have a negative balance (creating money).
        """
        if amount > 0:
            self.wallet.subtract(amount, currency, memo="Withdraw")
