import logging
from typing import Any, List, Optional, Dict, TYPE_CHECKING
import numpy as np
from modules.finance.api import InsufficientFundsError, IFinancialAgent, IFinancialEntity, IBank, ICentralBank, OMOInstructionDTO
from modules.finance.wallet.wallet import Wallet
from modules.finance.wallet.api import IWallet
from modules.system.api import ICurrencyHolder, CurrencyCode, DEFAULT_CURRENCY, MarketSnapshotDTO
from modules.system.constants import ID_CENTRAL_BANK
from modules.finance.engines.monetary_engine import MonetaryEngine
from modules.finance.engines.api import MonetaryStateDTO
from simulation.models import Order, Transaction

if TYPE_CHECKING:
    from modules.memory.api import MemoryV2Interface
    from simulation.dtos.strategy import ScenarioStrategy

logger = logging.getLogger(__name__)

class CentralBank(ICurrencyHolder, IFinancialAgent, IFinancialEntity, ICentralBank):
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

        self.monetary_engine = MonetaryEngine(config_module)

        logger.info(
            f"CENTRAL_BANK_INIT | Rate: {self.base_rate:.2%}, Target Infl: {self.inflation_target:.2%}",
            extra={"tick": 0, "tags": ["central_bank", "init"]}
        )

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
        Calculates interest rate using MonetaryEngine (Taylor Rule).
        """
        # A. Calculate Inflation
        price_history = self.tracker.metrics.get("avg_goods_price", [])
        inflation_rate = 0.0
        if len(price_history) > self.update_interval:
            p_current = price_history[-1]
            p_prev = price_history[-self.update_interval]
            if p_prev > 0:
                ticks_per_year = getattr(self.config_module, "TICKS_PER_YEAR", 100)
                period_inflation = (p_current - p_prev) / p_prev
                inflation_rate = period_inflation * (ticks_per_year / self.update_interval)

        # B. Prepare Strategy Overrides
        override_target_rate = None
        rate_multiplier = None
        if self.strategy and self.strategy.is_active:
             override_target_rate = self.strategy.monetary_shock_target_rate
             rate_multiplier = self.strategy.base_interest_rate_multiplier

        # C. Construct DTOs
        state = MonetaryStateDTO(
            tick=current_tick,
            current_base_rate=self.base_rate,
            potential_gdp=self.potential_gdp,
            inflation_target=self.inflation_target,
            override_target_rate=override_target_rate,
            rate_multiplier=rate_multiplier
        )

        snapshot = MarketSnapshotDTO(
            tick=current_tick,
            market_signals={},
            market_data={
                "inflation_rate_annual": inflation_rate,
                "current_gdp": current_gdp
            }
        )

        # D. Call Engine
        decision = self.monetary_engine.calculate_rate(state, snapshot)

        # E. Apply Decision
        old_rate = self.base_rate
        self.base_rate = decision.new_base_rate

        # Logging (retained for consistency)
        # Re-calc output gap for logging only
        output_gap = 0.0
        if self.potential_gdp > 0:
            output_gap = (current_gdp - self.potential_gdp) / self.potential_gdp

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

    def deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deposits a given amount into the central bank's cash reserves."""
        if amount > 0:
            self.wallet.add(amount, currency, memo="Deposit")

    def mint(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        Mints new currency (adds to cash reserves).
        Alias for deposit but semantically distinct for Genesis Protocol.
        """
        self.deposit(amount, currency)

    def withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        Withdraws a given amount from the central bank's cash reserves.
        As a Fiat Currency Issuer, the Central Bank can have a negative balance (creating money).
        """
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

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.wallet.add(amount, currency, memo="Protocol Deposit")

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        # Central Bank can always withdraw (create money)
        self.wallet.subtract(amount, currency, memo="Protocol Withdraw")

    def execute_open_market_operation(self, instruction: OMOInstructionDTO) -> List[Order]:
        """
        Takes an instruction and creates market orders to fulfill it.
        """
        logger.info(f"CENTRAL_BANK | Executing OMO: {instruction}")
        return []

    def process_omo_settlement(self, transaction: Transaction) -> None:
        """
        Callback for OMO settlement.
        """
        logger.info(f"CENTRAL_BANK | OMO Settlement processed: {transaction.transaction_id}")
