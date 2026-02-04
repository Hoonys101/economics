import logging
import warnings
from typing import Dict, List, Any, Deque, Tuple, Optional, TYPE_CHECKING
from collections import deque
from simulation.ai.enums import PoliticalParty
from simulation.interfaces.policy_interface import IGovernmentPolicy
from simulation.policies.taylor_rule_policy import TaylorRulePolicy
from simulation.policies.smart_leviathan_policy import SmartLeviathanPolicy
from simulation.dtos import GovernmentStateDTO
from simulation.dtos.api import MarketSnapshotDTO
from simulation.utils.shadow_logger import log_shadow
from simulation.models import Transaction
from simulation.systems.ministry_of_education import MinistryOfEducation
from simulation.portfolio import Portfolio
from modules.government.taxation.system import TaxationSystem
from modules.finance.api import InsufficientFundsError, TaxCollectionResult, IPortfolioHandler, PortfolioDTO, PortfolioAsset
from modules.government.components.fiscal_policy_manager import FiscalPolicyManager
from modules.government.dtos import FiscalPolicyDTO
from modules.government.components.welfare_manager import WelfareManager
from modules.government.components.infrastructure_manager import InfrastructureManager
from modules.government.constants import *
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY, ICurrencyHolder # Added for Phase 33

if TYPE_CHECKING:
    from simulation.finance.api import ISettlementSystem
    from modules.finance.api import BailoutLoanDTO
    from simulation.dtos.strategy import ScenarioStrategy
    from simulation.agents.central_bank import CentralBank

logger = logging.getLogger(__name__)

class Government(ICurrencyHolder):
    """
    정부 에이전트. 세금을 징수하고 보조금을 지급하거나 인프라에 투자합니다.
    """

    def __init__(self, id: int, initial_assets: float = 0.0, config_module: Any = None, strategy: Optional["ScenarioStrategy"] = None):
        self.id = id
        self._assets: Dict[CurrencyCode, float] = {}
        if isinstance(initial_assets, dict):
            self._assets = initial_assets.copy()
        else:
            self._assets[DEFAULT_CURRENCY] = float(initial_assets)
        self.config_module = config_module
        self.settlement_system: Optional["ISettlementSystem"] = None
        
        self.taxation_system = TaxationSystem(config_module)
        # self.tax_agency = TaxAgency(config_module) # Deprecated/Removed
        self.fiscal_policy_manager = FiscalPolicyManager(config_module)
        self.ministry_of_education = MinistryOfEducation(config_module)

        # New Managers
        self.welfare_manager = WelfareManager(self)
        self.infrastructure_manager = InfrastructureManager(self)

        # Initialize default fiscal policy
        # NOTE: Initialized with empty snapshot. Will be updated with real market data in the first tick
        # via make_policy_decision() before any tax collection occurs.
        self.fiscal_policy: FiscalPolicyDTO = self.fiscal_policy_manager.determine_fiscal_stance(
            MarketSnapshotDTO(tick=0, market_signals={}, market_data={})
        )

        self.total_collected_tax: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.total_spent_subsidies: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.infrastructure_level: int = 0

        # Money Tracking (Gold Standard & Fractional Reserve)
        self.total_money_issued: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.total_money_destroyed: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.start_tick_money_issued: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.start_tick_money_destroyed: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        # WO-024: Fractional Reserve Credit Tracking
        self.credit_delta_this_tick: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        
        # 세수 유형별 집계
        self.tax_revenue: Dict[str, float] = {}

        # --- Phase 7: Adaptive Fiscal Policy State ---
        self.potential_gdp: float = 0.0
        self.gdp_ema: float = 0.0
        self.fiscal_stance: float = 0.0

        # --- Phase 24: Policy Strategy Selection ---
        policy_mode = getattr(config_module, "GOVERNMENT_POLICY_MODE", "TAYLOR_RULE")
        if policy_mode == "AI_ADAPTIVE":
            self.policy_engine: IGovernmentPolicy = SmartLeviathanPolicy(self, config_module)
        else:
            self.policy_engine: IGovernmentPolicy = TaylorRulePolicy(config_module)

        # Legacy / Compatibility
        self.ai = getattr(self.policy_engine, "ai", None)

        # Political State
        self.ruling_party: PoliticalParty = PoliticalParty.BLUE # Default
        self.approval_rating: float = 0.5
        self.public_opinion_queue: Deque[float] = deque(maxlen=4) # 4-tick lag
        self.perceived_public_opinion: float = 0.5
        self.last_election_tick: int = 0

        # Policy Levers (Tax Rates)
        self.income_tax_rate: float = getattr(config_module, "INCOME_TAX_RATE", 0.1)
        self.corporate_tax_rate: float = getattr(config_module, "CORPORATE_TAX_RATE", 0.2)

        # WO-136: Strategy Initialization Overrides (Legacy Support)
        if strategy:
             if strategy.initial_income_tax_rate is not None:
                 self.income_tax_rate = strategy.initial_income_tax_rate
             if strategy.initial_corporate_tax_rate is not None:
                 self.corporate_tax_rate = strategy.initial_corporate_tax_rate

        # WO-136: Apply Strategy Overrides
        if strategy and strategy.is_active:
             if strategy.fiscal_shock_tax_rate is not None:
                 self.corporate_tax_rate = strategy.fiscal_shock_tax_rate

             if strategy.corporate_tax_rate_delta is not None:
                 self.corporate_tax_rate += strategy.corporate_tax_rate_delta

        # Spending Multipliers (AI Controlled)
        # 1.0 = Normal (Budget Neutral-ish), >1.0 = Stimulus, <1.0 = Austerity
        self.welfare_budget_multiplier: float = 1.0
        self.firm_subsidy_budget_multiplier: float = 1.0

        self.effective_tax_rate: float = self.income_tax_rate # Legacy compatibility
        self.total_debt: float = 0.0
        # ---------------------------------------------

        # History buffers for visualization
        self.tax_history: List[Dict[str, Any]] = [] # For Stacked Bar Chart (breakdown per tick)
        self.welfare_history: List[Dict[str, float]] = [] # For Welfare Line Chart
        self.history_window_size = 5000

        # Current tick accumulators (reset every tick)
        self.current_tick_stats = {
            "tax_revenue": {},
            "welfare_spending": 0.0,
            "stimulus_spending": 0.0,
            "total_collected": 0.0,
            "education_spending": 0.0 # WO-054
        }

        # GDP Tracking for Stimulus
        self.gdp_history: List[float] = []
        self.gdp_history_window = 20
        
        # WO-056: Shadow Policy Metrics
        ticks_per_year = int(getattr(config_module, "TICKS_PER_YEAR", DEFAULT_TICKS_PER_YEAR))
        self.price_history_shadow: Deque[float] = deque(maxlen=ticks_per_year)

        self.revenue_this_tick: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.expenditure_this_tick: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.revenue_breakdown_this_tick: Dict[str, float] = {}
        
        self.average_approval_rating = 0.5

        # WO-057-B: Sensory Data Container
        self.sensory_data: Optional[GovernmentStateDTO] = None
        self.finance_system = None

        # Analysis Hook for Phenomena Reporting (TD-154)
        self.last_fiscal_activation_tick: int = -1

        # TD-160: Portfolio for holding escheated assets
        self.portfolio = Portfolio(self.id)

        logger.info(
            f"Government {self.id} initialized with assets: {self.assets}",
            extra={"tick": 0, "agent_id": self.id, "tags": ["init", "government"]},
        )

    @property
    def assets(self) -> Dict[CurrencyCode, float]:
        """Returns the government's liquid assets."""
        return self._assets

    def get_assets_by_currency(self) -> Dict[CurrencyCode, float]:
        """Implementation of ICurrencyHolder."""
        return self._assets.copy()

    def _internal_add_assets(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        [INTERNAL ONLY] Increase assets.
        """
        if currency not in self._assets:
            self._assets[currency] = 0.0
        self._assets[currency] += amount

    def _internal_sub_assets(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        [INTERNAL ONLY] Decrease assets.
        """
        if currency not in self._assets:
            self._assets[currency] = 0.0
        self._assets[currency] -= amount

    def update_sensory_data(self, dto: GovernmentStateDTO):
        """
        WO-057-B: Sensory Module Interface.
        Receives 10-tick SMA macro data from the Engine.
        """
        self.sensory_data = dto
        # Log reception (Debug)
        if dto.tick % 50 == 0:
            inf_sma = dto.inflation_sma if isinstance(dto.inflation_sma, (int, float)) else 0.0
            app_sma = dto.approval_sma if isinstance(dto.approval_sma, (int, float)) else 0.0
            logger.debug(
                f"SENSORY_UPDATE | Government received macro data. Inflation_SMA: {inf_sma:.4f}, Approval_SMA: {app_sma:.2f}",
                extra={"tick": dto.tick, "agent_id": self.id, "tags": ["sensory", "wo-057-b"]}
            )

    def calculate_income_tax(self, income: float, survival_cost: float) -> float:
        """
        Calculates income tax using the FiscalPolicyManager and current policy.
        """
        if self.fiscal_policy:
            return self.fiscal_policy_manager.calculate_tax_liability(self.fiscal_policy, income)

        # Fallback (should not happen if initialized correctly)
        tax_mode = getattr(self.config_module, "TAX_MODE", "PROGRESSIVE")
        return self.taxation_system.calculate_income_tax(income, survival_cost, self.income_tax_rate, tax_mode)

    def calculate_corporate_tax(self, profit: float) -> float:
        """Delegates corporate tax calculation to the TaxationSystem."""
        return self.taxation_system.calculate_corporate_tax(profit, self.corporate_tax_rate)

    def reset_tick_flow(self):
        """
        매 틱 시작 시 호출되어 이번 틱의 Flow 데이터를 초기화하고,
        이전 틱의 데이터를 History에 저장합니다.
        """
        if getattr(self, "revenue_breakdown_this_tick", None) is None:
             self.revenue_breakdown_this_tick = {}

        self.revenue_this_tick = {DEFAULT_CURRENCY: 0.0}
        self.expenditure_this_tick = {DEFAULT_CURRENCY: 0.0}
        self.credit_delta_this_tick = {DEFAULT_CURRENCY: 0.0}
        self.revenue_breakdown_this_tick = {}

        # Snapshot for delta calculation
        self.start_tick_money_issued = self.total_money_issued.copy()
        self.start_tick_money_destroyed = self.total_money_destroyed.copy()

    def process_monetary_transactions(self, transactions: List[Transaction]):
        """
        Processes transactions related to monetary policy (Credit Creation/Destruction).
        Called by the orchestrator or systems generating these transactions.
        """
        for tx in transactions:
            cur = getattr(tx, 'currency', DEFAULT_CURRENCY)
            if tx.transaction_type == "credit_creation":
                if cur not in self.credit_delta_this_tick: self.credit_delta_this_tick[cur] = 0.0
                if cur not in self.total_money_issued: self.total_money_issued[cur] = 0.0
                self.credit_delta_this_tick[cur] += tx.price
                self.total_money_issued[cur] += tx.price
                logger.debug(f"MONETARY_EXPANSION | Credit created: {tx.price:.2f} {cur}")
            elif tx.transaction_type == "credit_destruction":
                if cur not in self.credit_delta_this_tick: self.credit_delta_this_tick[cur] = 0.0
                if cur not in self.total_money_destroyed: self.total_money_destroyed[cur] = 0.0
                self.credit_delta_this_tick[cur] -= tx.price
                self.total_money_destroyed[cur] += tx.price
                logger.debug(f"MONETARY_CONTRACTION | Credit destroyed: {tx.price:.2f} {cur}")

    def collect_tax(self, amount: float, tax_type: str, payer: Any, current_tick: int) -> "TaxCollectionResult":
        """
        Legacy adapter method used by TransactionProcessor.

        DEPRECATED: Direct usage of this method is discouraged.
        """
        warnings.warn(
            "Government.collect_tax is deprecated. Use settlement.settle_atomic and government.record_revenue() instead.",
            DeprecationWarning,
            stacklevel=2
        )

        payer_id = payer.id if hasattr(payer, 'id') else str(payer)

        if not self.settlement_system:
            logger.error("Government has no SettlementSystem linked. Cannot collect tax.")
            return {
                "success": False,
                "amount_collected": 0.0,
                "tax_type": tax_type,
                "payer_id": payer_id,
                "payee_id": self.id,
                "error_message": "No SettlementSystem linked"
            }

        # Execute atomic transfer directly via SettlementSystem (Internal logic)
        # Using transfer() for single payment
        success = self.settlement_system.transfer(payer, self, amount, f"{tax_type} collection")

        result = {
            "success": bool(success),
            "amount_collected": amount if success else 0.0,
            "tax_type": tax_type,
            "payer_id": payer_id,
            "payee_id": self.id,
            "error_message": None if success else "Transfer failed"
        }

        # Record stats
        self.record_revenue(result)

        return result

    def record_revenue(self, result: "TaxCollectionResult"):
        """
        [NEW] Updates the government's internal ledgers based on a verified
        TaxCollectionResult DTO.
        """
        if not result['success'] or result['amount_collected'] <= 0:
            return

        amount = result['amount_collected']
        tax_type = result['tax_type']
        payer_id = result['payer_id']
        cur = result.get('currency', DEFAULT_CURRENCY)

        if cur not in self.total_collected_tax: self.total_collected_tax[cur] = 0.0
        if cur not in self.revenue_this_tick: self.revenue_this_tick[cur] = 0.0
        
        self.total_collected_tax[cur] += amount
        self.revenue_this_tick[cur] += amount
        self.tax_revenue[tax_type] = (
            self.tax_revenue.get(tax_type, 0.0) + amount
        )
        self.current_tick_stats["tax_revenue"][tax_type] = (
            self.current_tick_stats["tax_revenue"].get(tax_type, 0.0) + amount
        )
        self.current_tick_stats["total_collected"] += amount

    def update_public_opinion(self, households: List[Any]):
        """
        Aggregates approval ratings from households and updates the opinion queue (Lag).
        """
        total_approval = 0
        count = 0
        for h in households:
            if h._bio_state.is_active:
                # Household must have 'approval_rating' (0 or 1)
                rating = h._social_state.approval_rating
                total_approval += rating
                count += 1

        avg_approval = total_approval / count if count > 0 else 0.5
        self.public_opinion_queue.append(avg_approval)

        if len(self.public_opinion_queue) > 0:
            self.perceived_public_opinion = self.public_opinion_queue[0]

        self.approval_rating = avg_approval

    def check_election(self, current_tick: int):
        """
        Checks for election cycle and handles regime change.
        """
        election_cycle = 100
        if current_tick > 0 and current_tick % election_cycle == 0:
            self.last_election_tick = current_tick

            if self.perceived_public_opinion < 0.5:
                # Flip Party
                old_party = self.ruling_party
                self.ruling_party = PoliticalParty.RED if old_party == PoliticalParty.BLUE else PoliticalParty.BLUE

                logger.warning(
                    f"ELECTION_RESULTS | REGIME CHANGE! {old_party.name} -> {self.ruling_party.name}. Approval: {self.perceived_public_opinion:.2f}",
                    extra={"tick": current_tick, "agent_id": self.id, "tags": ["election", "regime_change"]}
                )
            else:
                logger.info(
                    f"ELECTION_RESULTS | INCUMBENT VICTORY ({self.ruling_party.name}). Approval: {self.perceived_public_opinion:.2f}",
                    extra={"tick": current_tick, "agent_id": self.id, "tags": ["election"]}
                )

    def make_policy_decision(self, market_data: Dict[str, Any], current_tick: int, central_bank: "CentralBank"):
        """
        정책 엔진에게 의사결정을 위임하고 결과를 반영합니다.
        (전략 패턴 적용: Taylor Rule 또는 AI Adaptive)
        """
        # 0. Update Fiscal Policy (WO-145)
        # WO-147: Check if fiscal stabilizer is enabled (default True)
        if getattr(self.config_module, "ENABLE_FISCAL_STABILIZER", True):
            # Convert market_data dict to MarketSnapshotDTO for FiscalPolicyManager
            snapshot = MarketSnapshotDTO(
                tick=current_tick,
                market_signals={},
                market_data=market_data
            )
            self.fiscal_policy = self.fiscal_policy_manager.determine_fiscal_stance(snapshot)

        # 1. 정책 엔진 실행 (Actuator 및 Shadow Mode 로직 포함)
        decision = self.policy_engine.decide(self, self.sensory_data, current_tick, central_bank)
        
        if decision.get("status") == "EXECUTED":
             logger.debug(
                f"POLICY_EXECUTED | Tick: {current_tick} | Action: {decision.get('action_taken')}",
                extra={"tick": current_tick, "agent_id": self.id}
            )

        gdp_gap = 0.0
        if self.potential_gdp > 0:
            current_gdp = market_data.get("total_production", 0.0)
            gdp_gap = (current_gdp - self.potential_gdp) / self.potential_gdp

            alpha = 0.01
            self.potential_gdp = (alpha * current_gdp) + ((1-alpha) * self.potential_gdp)

        # 1. Calculate Inflation (YoY)
        inflation = 0.0
        if len(self.price_history_shadow) >= 2:
            current_p = self.price_history_shadow[-1]
            past_p = self.price_history_shadow[0]
            if past_p > 0:
                inflation = (current_p - past_p) / past_p

        # 2. Calculate Real GDP Growth
        real_gdp_growth = 0.0
        if len(self.gdp_history) >= 2:
            current_gdp = self.gdp_history[-1]
            past_gdp = self.gdp_history[-2]
            if past_gdp > 0:
                real_gdp_growth = (current_gdp - past_gdp) / past_gdp

        target_inflation = getattr(self.config_module, "CB_INFLATION_TARGET", 0.02)
        neutral_rate = max(0.01, real_gdp_growth)
        target_rate = neutral_rate + inflation + 0.5 * (inflation - target_inflation) + 0.5 * gdp_gap

        current_base_rate = 0.05
        if "loan_market" in market_data:
            current_base_rate = market_data["loan_market"].get("interest_rate", 0.05)

        gap = target_rate - current_base_rate

        log_shadow(
            tick=current_tick,
            agent_id=self.id,
            agent_type="Government",
            metric="taylor_rule_rate",
            current_value=current_base_rate,
            shadow_value=target_rate,
            details=f"Inf={inflation:.2%}, Growth={real_gdp_growth:.2%}, Gap={gdp_gap:.2%}, RateGap={gap:.4f}"
        )

    def provide_household_support(self, household: Any, amount: float, current_tick: int) -> List[Transaction]:
        """Delegates to WelfareManager."""
        return self.welfare_manager.provide_household_support(household, amount, current_tick)

    def provide_firm_bailout(self, firm: Any, amount: float, current_tick: int) -> Tuple[Optional["BailoutLoanDTO"], List[Transaction]]:
        """Provides a bailout loan to a firm if it's eligible. Returns (LoanDTO, Transactions)."""
        if self.finance_system.evaluate_solvency(firm, current_tick):
            logger.info(f"BAILOUT_APPROVED | Firm {firm.id} is eligible for a bailout.")
            # FinanceSystem now returns (loan, transactions)
            loan, txs = self.finance_system.grant_bailout_loan(firm, amount, current_tick)
            if loan:
                cur = getattr(loan, 'currency', DEFAULT_CURRENCY)
                if cur not in self.expenditure_this_tick: self.expenditure_this_tick[cur] = 0.0
                self.expenditure_this_tick[cur] += amount
            return loan, txs
        else:
            logger.warning(f"BAILOUT_DENIED | Firm {firm.id} is insolvent and not eligible for a bailout.")
            return None, []

    def get_survival_cost(self, market_data: Dict[str, Any]) -> float:
        """ Calculates current survival cost based on food prices. Delegates to WelfareManager. """
        return self.welfare_manager.get_survival_cost(market_data)

    def run_welfare_check(self, agents: List[Any], market_data: Dict[str, Any], current_tick: int) -> List[Transaction]:
        """
        Delegates to WelfareManager.
        """
        return self.welfare_manager.run_welfare_check(agents, market_data, current_tick)

    def invest_infrastructure(self, current_tick: int, households: List[Any] = None) -> List[Transaction]:
        """
        Delegates to InfrastructureManager.
        """
        return self.infrastructure_manager.invest_infrastructure(current_tick, households)

    def finalize_tick(self, current_tick: int):
        """
        Called at the end of every tick to finalize statistics and push to history buffers.
        """
        revenue_snapshot = self.current_tick_stats["tax_revenue"].copy()
        revenue_snapshot["tick"] = current_tick
        # For simplicity, snapshot uses USD or sums main currency
        revenue_snapshot["total"] = self.current_tick_stats["total_collected"]

        # WO-057 Deficit Spending: Update total_debt based on FinanceSystem
        if self.finance_system:
             self.total_debt = sum(b.face_value for b in self.finance_system.outstanding_bonds)
        elif self.assets < 0:
             self.total_debt = abs(self.assets)
        else:
             self.total_debt = 0.0

        self.tax_history.append(revenue_snapshot)
        if len(self.tax_history) > self.history_window_size:
            self.tax_history.pop(0)

        welfare_snapshot = {
            "tick": current_tick,
            "welfare": self.current_tick_stats["welfare_spending"],
            "stimulus": self.current_tick_stats["stimulus_spending"],
            "education": self.current_tick_stats.get("education_spending", 0.0), # WO-054
            "debt": self.total_debt,
            "assets": self.assets
        }
        self.welfare_history.append(welfare_snapshot)
        if len(self.welfare_history) > self.history_window_size:
            self.welfare_history.pop(0)

        self.current_tick_stats = {
            "tax_revenue": {},
            "welfare_spending": 0.0,
            "stimulus_spending": 0.0,
            "education_spending": 0.0, # WO-054
            "total_collected": 0.0
        }

    def get_monetary_delta(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> float:
        """
        Returns the net change in the money supply authorized this tick for a specific currency.
        """
        issued_delta = self.total_money_issued.get(currency, 0.0) - self.start_tick_money_issued.get(currency, 0.0)
        destroyed_delta = self.total_money_destroyed.get(currency, 0.0) - self.start_tick_money_destroyed.get(currency, 0.0)
        return issued_delta - destroyed_delta

    def get_agent_data(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_type": "government",
            "assets": self.assets,
            "ruling_party": self.ruling_party.name,
            "approval_rating": self.approval_rating,
            "income_tax_rate": self.income_tax_rate,
            "corporate_tax_rate": self.corporate_tax_rate,
            "perceived_public_opinion": self.perceived_public_opinion
        }

    def get_debt_to_gdp_ratio(self) -> float:
        """Calculates the debt-to-GDP ratio."""
        if not self.sensory_data or self.sensory_data.current_gdp == 0:
            return 0.0

        debt = max(0.0, -self.assets)
        return debt / self.sensory_data.current_gdp

    def deposit(self, amount: float, currency: str = None) -> None:
        """Deposits a given amount into the government's assets."""
        if amount > 0:
            self._internal_add_assets(amount, currency=currency or DEFAULT_CURRENCY)

    def withdraw(self, amount: float, currency: str = None) -> None:
        """Withdraws a given amount from the government's assets."""
        currency = currency or DEFAULT_CURRENCY
        if amount > 0:
            current_assets = self._assets.get(currency, 0.0)
            if current_assets < amount:
                raise InsufficientFundsError(f"Government {self.id} has insufficient funds for withdrawal of {amount:.2f} {currency}. Available: {current_assets:.2f}")
            self._internal_sub_assets(amount, currency=currency)

    # WO-054: Public Education System
    def run_public_education(self, agents: List[Any], config_module: Any, current_tick: int) -> List[Transaction]:
        """
        Delegates public education logic to the Ministry of Education.
        Returns transactions.
        """
        households = [a for a in agents if hasattr(a, '_econ_state')]
        return self.ministry_of_education.run_public_education(households, self, current_tick)

    # --- IPortfolioHandler Implementation (TD-160) ---

    def get_portfolio(self) -> PortfolioDTO:
        assets = []
        for firm_id, share in self.portfolio.holdings.items():
            assets.append(PortfolioAsset(
                asset_type="stock",
                asset_id=str(firm_id),
                quantity=share.quantity
            ))
        return PortfolioDTO(assets=assets)

    def receive_portfolio(self, portfolio: PortfolioDTO) -> None:
        """
        Receives escheated assets.
        """
        for asset in portfolio.assets:
            if asset.asset_type == "stock":
                try:
                    firm_id = int(asset.asset_id)
                    # Government integrates assets.
                    # Note: Ideally Government might sell them later (Privatization).
                    self.portfolio.add(firm_id, asset.quantity, 0.0)
                except ValueError:
                    logger.error(f"Invalid firm_id in portfolio receive: {asset.asset_id}")
            else:
                logger.warning(f"Government received unhandled asset type: {asset.asset_type} (ID: {asset.asset_id})")

    def clear_portfolio(self) -> None:
        self.portfolio.holdings.clear()
