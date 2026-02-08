import logging
import warnings
from typing import Dict, List, Any, Deque, Tuple, Optional, TYPE_CHECKING
from collections import deque
from simulation.ai.enums import PoliticalParty, PolicyActionTag, EconomicSchool
from simulation.interfaces.policy_interface import IGovernmentPolicy
from simulation.policies.taylor_rule_policy import TaylorRulePolicy
from simulation.policies.smart_leviathan_policy import SmartLeviathanPolicy
from simulation.policies.adaptive_gov_policy import AdaptiveGovPolicy
from simulation.dtos import GovernmentStateDTO
from simulation.dtos.api import MarketSnapshotDTO
from simulation.dtos.policy_dtos import PolicyContextDTO, PolicyDecisionResultDTO
from simulation.utils.shadow_logger import log_shadow
from simulation.models import Transaction
from simulation.systems.ministry_of_education import MinistryOfEducation
from simulation.portfolio import Portfolio
from modules.finance.api import InsufficientFundsError, TaxCollectionResult, IPortfolioHandler, PortfolioDTO, PortfolioAsset, IFinancialEntity
from modules.government.dtos import (
    FiscalPolicyDTO,
    PaymentRequestDTO,
    WelfareResultDTO,
    BailoutResultDTO
)
from modules.government.welfare.manager import WelfareManager
from modules.government.tax.service import TaxService
from modules.government.tax.api import ITaxService
from modules.government.components.infrastructure_manager import InfrastructureManager
from modules.government.constants import *
from modules.government.components.monetary_ledger import MonetaryLedger
from modules.government.components.policy_lockout_manager import PolicyLockoutManager
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY, ICurrencyHolder # Added for Phase 33
from modules.finance.wallet.wallet import Wallet
from modules.finance.wallet.api import IWallet

if TYPE_CHECKING:
    from simulation.finance.api import ISettlementSystem
    from modules.finance.api import BailoutLoanDTO
    from simulation.dtos.strategy import ScenarioStrategy
    from simulation.agents.central_bank import CentralBank

logger = logging.getLogger(__name__)

class Government(ICurrencyHolder, IFinancialEntity):
    """
    정부 에이전트. 세금을 징수하고 보조금을 지급하거나 인프라에 투자합니다.
    """

    def __init__(self, id: int, initial_assets: float = 0.0, config_module: Any = None, strategy: Optional["ScenarioStrategy"] = None):
        self.id = id

        initial_balance_dict = {}
        if isinstance(initial_assets, dict):
            initial_balance_dict = initial_assets.copy()
        else:
            initial_balance_dict[DEFAULT_CURRENCY] = float(initial_assets)

        self.wallet = Wallet(self.id, initial_balance_dict)

        self.config_module = config_module
        self.settlement_system: Optional["ISettlementSystem"] = None
        
        # Facade Services
        self.tax_service: ITaxService = TaxService(config_module)
        self.welfare_manager = WelfareManager(config_module)

        self.ministry_of_education = MinistryOfEducation(config_module)
        self.infrastructure_manager = InfrastructureManager(self)
        self.monetary_ledger = MonetaryLedger()
        self.policy_lockout_manager = PolicyLockoutManager()

        # Initialize default fiscal policy
        # NOTE: Initialized with empty snapshot. Will be updated with real market data in the first tick
        # via make_policy_decision() before any tax collection occurs.
        self.fiscal_policy: FiscalPolicyDTO = self.tax_service.determine_fiscal_stance(
            MarketSnapshotDTO(tick=0, market_signals={}, market_data={})
        )

        self.total_spent_subsidies: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.infrastructure_level: int = 0

        # --- Phase 7: Adaptive Fiscal Policy State ---
        self.potential_gdp: float = 0.0
        self.gdp_ema: float = 0.0
        self.fiscal_stance: float = 0.0

        # --- Phase 24: Policy Strategy Selection ---
        policy_mode = getattr(config_module, "GOVERNMENT_POLICY_MODE", "TAYLOR_RULE")
        if policy_mode == "AI_ADAPTIVE":
            self.policy_engine: IGovernmentPolicy = AdaptiveGovPolicy(self, config_module)
        elif policy_mode == "AI_LEGACY":
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

        self.gdp_history: List[float] = []
        self.gdp_history_window = 20
        
        # WO-056: Shadow Policy Metrics
        ticks_per_year = int(getattr(config_module, "TICKS_PER_YEAR", DEFAULT_TICKS_PER_YEAR))
        self.price_history_shadow: Deque[float] = deque(maxlen=ticks_per_year)

        self.expenditure_this_tick: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        
        self.average_approval_rating = 0.5

        # WO-057-B: Sensory Data Container
        self.sensory_data: Optional[GovernmentStateDTO] = None
        self.finance_system = None

        # Analysis Hook for Phenomena Reporting (TD-154)
        self.last_fiscal_activation_tick: int = -1

        # TD-160: Portfolio for holding escheated assets
        self.portfolio = Portfolio(self.id)

        logger.info(
            f"Government {self.id} initialized with assets: {self.wallet.get_all_balances()}",
            extra={"tick": 0, "agent_id": self.id, "tags": ["init", "government"]},
        )

    # --- IFinancialEntity Implementation ---

    @property
    def assets(self) -> float:
        """Returns the government's liquid assets in DEFAULT_CURRENCY."""
        return self.wallet.get_balance(DEFAULT_CURRENCY)

    @property
    def total_collected_tax(self) -> Dict[CurrencyCode, float]:
        """Accessor for total collected tax from TaxService."""
        return self.tax_service.get_total_collected_tax()

    @property
    def revenue_this_tick(self) -> Dict[CurrencyCode, float]:
        """Accessor for revenue this tick from TaxService."""
        return self.tax_service.get_revenue_this_tick()

    @property
    def tax_revenue(self) -> Dict[str, float]:
        """Accessor for tax revenue breakdown from TaxService."""
        return self.tax_service.get_tax_revenue()

    def get_assets_by_currency(self) -> Dict[CurrencyCode, float]:
        """Implementation of ICurrencyHolder."""
        return self.wallet.get_all_balances()

    def _internal_add_assets(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        [INTERNAL ONLY] Increase assets.
        """
        self.wallet.add(amount, currency, memo="Internal Add")

    def _internal_sub_assets(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        [INTERNAL ONLY] Decrease assets.
        """
        self.wallet.subtract(amount, currency, memo="Internal Sub")

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
        Calculates income tax using the TaxService and current policy.
        """
        return self.tax_service.calculate_tax_liability(self.fiscal_policy, income)

    def calculate_corporate_tax(self, profit: float) -> float:
        """Delegates corporate tax calculation to the TaxService."""
        return self.tax_service.calculate_corporate_tax(profit, self.corporate_tax_rate)

    def reset_tick_flow(self):
        """
        매 틱 시작 시 호출되어 이번 틱의 Flow 데이터를 초기화하고,
        이전 틱의 데이터를 History에 저장합니다.
        """
        self.tax_service.reset_tick_flow()
        self.welfare_manager.reset_tick_flow()
        self.monetary_ledger.reset_tick_flow()

        self.expenditure_this_tick = {DEFAULT_CURRENCY: 0.0}

    def record_gdp(self, gdp: float) -> None:
        """
        Records the GDP for the current tick.
        Encapsulates gdp_history mutation (TD-234).
        """
        self.gdp_history.append(gdp)
        if len(self.gdp_history) > self.gdp_history_window:
            self.gdp_history.pop(0)

    def process_monetary_transactions(self, transactions: List[Transaction]):
        """
        Delegates monetary transaction processing to the MonetaryLedger.
        DEPRECATED: Should be called via Phase_MonetaryProcessing -> MonetaryLedger directly.
        Kept for backward compatibility if any direct calls remain.
        """
        self.monetary_ledger.process_transactions(transactions)

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
        Updates the government's internal ledgers via TaxService.
        """
        self.tax_service.record_revenue(result)

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
            self.fiscal_policy = self.tax_service.determine_fiscal_stance(snapshot)
            # Inject dynamic tax rates from Government state into the policy DTO
            self.fiscal_policy.corporate_tax_rate = self.corporate_tax_rate
            self.fiscal_policy.income_tax_rate = self.income_tax_rate

        # 1. Create PolicyContextDTO
        locked_tags = self.policy_lockout_manager.get_locked_tags(current_tick) if hasattr(self.policy_lockout_manager, 'get_locked_tags') else []
        
        cb_rate = central_bank.get_base_rate() if central_bank else 0.05

        context = PolicyContextDTO(
            agent_id=self.id,
            tick=current_tick,
            sensory_data=self.sensory_data,
            central_bank_base_rate=cb_rate,
            locked_policies=locked_tags,
            current_welfare_budget_multiplier=self.welfare_budget_multiplier,
            current_corporate_tax_rate=self.corporate_tax_rate,
            current_income_tax_rate=self.income_tax_rate,
            potential_gdp=self.potential_gdp,
            fiscal_stance=self.fiscal_stance,
            ruling_party=self.ruling_party
        )

        # 2. Call Decide
        result = self.policy_engine.decide(context)

        if result.status == "EXECUTED":
             logger.debug(
                f"POLICY_EXECUTED | Tick: {current_tick} | Action: {result.action_taken}",
                extra={"tick": current_tick, "agent_id": self.id}
            )

        # 3. Apply Result
        if result.updated_potential_gdp is not None:
            self.potential_gdp = result.updated_potential_gdp

        if result.updated_fiscal_stance is not None:
            self.fiscal_stance = result.updated_fiscal_stance

        if result.updated_income_tax_rate is not None:
            self.income_tax_rate = result.updated_income_tax_rate

        if result.updated_corporate_tax_rate is not None:
            self.corporate_tax_rate = result.updated_corporate_tax_rate

        if result.updated_welfare_budget_multiplier is not None:
            self.welfare_budget_multiplier = result.updated_welfare_budget_multiplier

        if result.interest_rate_target is not None:
            if result.policy_type == "AI_ADAPTIVE" and central_bank:
                 central_bank.set_base_rate(result.interest_rate_target)

        if result.action_request:
            if result.action_request.action_type == "FIRE_ADVISOR":
                self.fire_advisor(result.action_request.target, current_tick)

    SCHOOL_TO_POLICY_MAP = {
        EconomicSchool.KEYNESIAN: [PolicyActionTag.KEYNESIAN_FISCAL],
        EconomicSchool.AUSTRIAN: [PolicyActionTag.AUSTRIAN_AUSTERITY],
        EconomicSchool.MONETARIST: [PolicyActionTag.MONETARIST_RULES],
    }

    def fire_advisor(self, school: EconomicSchool, current_tick: int) -> None:
        """
        Fires the advisor of a specific economic school and locks associated policies.
        Decoupled mapping via SCHOOL_TO_POLICY_MAP (TD-224).
        """
        duration = 20
        tags_to_lock = self.SCHOOL_TO_POLICY_MAP.get(school, [])

        if not tags_to_lock:
            logger.warning(
                f"ADVISOR_FIRED | Fired {school.name} advisor but no policies to lock found.",
                extra={"tick": current_tick, "agent_id": self.id}
            )
            return

        for tag in tags_to_lock:
            self.policy_lockout_manager.lock_policy(tag, duration, current_tick)

        logger.info(
            f"ADVISOR_FIRED | Fired {school.name} advisor. Locked tags: {[t.name for t in tags_to_lock]} for {duration} ticks.",
            extra={"tick": current_tick, "agent_id": self.id}
        )

    def provide_household_support(self, household: Any, amount: float, current_tick: int) -> List[Transaction]:
        """
        Manually executes household support (legacy support).
        """
        # Scapegoat Lockout Check: Keynesian Fiscal (Stimulus)
        if self.policy_lockout_manager.is_locked(PolicyActionTag.KEYNESIAN_FISCAL, current_tick):
            return []

        effective_amount = amount * self.welfare_budget_multiplier
        if effective_amount <= 0:
            return []

        # Funding Logic (Simplified from old WelfareService)
        current_balance = self.wallet.get_balance(DEFAULT_CURRENCY)
        if current_balance < effective_amount:
             if self.finance_system:
                  self.finance_system.issue_treasury_bonds(effective_amount - current_balance, current_tick)

        success = self.settlement_system.transfer(self, household, effective_amount, "welfare_support")

        if success:
             return [Transaction(
                 buyer_id=self.id,
                 seller_id=household.id,
                 item_id="welfare_support",
                 quantity=1.0,
                 price=effective_amount,
                 market_id="system",
                 transaction_type="welfare",
                 time=current_tick
             )]
        return []

    def provide_firm_bailout(self, firm: Any, amount: float, current_tick: int) -> Tuple[Optional["BailoutLoanDTO"], List[Transaction]]:
        """Provides a bailout loan to a firm if it's eligible. Returns (LoanDTO, Transactions)."""
        # Scapegoat Lockout Check: Keynesian Fiscal (Bailout is Stimulus)
        if self.policy_lockout_manager.is_locked(PolicyActionTag.KEYNESIAN_FISCAL, current_tick):
            logger.info("BAILOUT_BLOCKED | Keynesian Fiscal Policy is locked.")
            return None, []

        is_solvent = self.finance_system.evaluate_solvency(firm, current_tick)

        # Use WelfareManager for eligibility/terms logic
        result = self.welfare_manager.provide_firm_bailout(firm, amount, current_tick, is_solvent)

        if result:
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
        snapshot = MarketSnapshotDTO(tick=0, market_signals={}, market_data=market_data)
        return self.welfare_manager.get_survival_cost(snapshot)

    def run_welfare_check(self, agents: List[Any], market_data: Dict[str, Any], current_tick: int) -> List[Transaction]:
        """
        Legacy entry point. Orchestrates Tax and Welfare via execute_social_policy.
        Returns empty list as transactions are executed atomically.
        """
        self.execute_social_policy(agents, market_data, current_tick)
        return []

    def execute_social_policy(self, agents: List[Any], market_data: Dict[str, Any], current_tick: int) -> None:
        """
        Orchestrates Tax Collection and Welfare Distribution.
        """
        # Convert market_data for services
        snapshot = MarketSnapshotDTO(
            tick=current_tick,
            market_signals={},
            market_data=market_data
        )

        # 1. Wealth Tax Logic (TaxService)
        tax_result = self.tax_service.collect_wealth_tax(agents)

        for req in tax_result.payment_requests:
            if self.settlement_system:
                # Execute atomic transfer
                success = self.settlement_system.transfer(req.payer, self, req.amount, req.memo, currency=req.currency)

                if success:
                     # Record revenue via TaxService
                     self.record_revenue({
                         "success": True,
                         "amount_collected": req.amount,
                         "tax_type": tax_result.tax_type,
                         "currency": req.currency,
                         "payer_id": req.payer.id if hasattr(req.payer, 'id') else req.payer,
                         "payee_id": self.id
                     })

        # 2. Welfare Check (WelfareManager)
        # Update GDP History
        current_gdp = market_data.get("total_production", 0.0)
        self.gdp_history.append(current_gdp)
        if len(self.gdp_history) > self.gdp_history_window:
            self.gdp_history.pop(0)

        welfare_result = self.welfare_manager.run_welfare_check(agents, snapshot, current_tick, self.gdp_history, self.welfare_budget_multiplier)

        # Funding Logic (Stimulus/Benefits)
        if welfare_result.total_paid > 0:
            current_balance = self.wallet.get_balance(DEFAULT_CURRENCY)
            if current_balance < welfare_result.total_paid:
                if self.finance_system:
                    self.finance_system.issue_treasury_bonds(welfare_result.total_paid - current_balance, current_tick)

        for req in welfare_result.payment_requests:
            if self.settlement_system:
                 self.settlement_system.transfer(self, req.payee, req.amount, req.memo, currency=req.currency)

    def invest_infrastructure(self, current_tick: int, households: List[Any] = None) -> List[Transaction]:
        """
        Delegates to InfrastructureManager.
        """
        return self.infrastructure_manager.invest_infrastructure(current_tick, households)

    def finalize_tick(self, current_tick: int):
        """
        Called at the end of every tick to finalize statistics and push to history buffers.
        """
        # Retrieve welfare spending from service
        welfare_spending = self.welfare_manager.get_spending_this_tick()

        # Update expenditure_this_tick (aggregate)
        if DEFAULT_CURRENCY not in self.expenditure_this_tick:
            self.expenditure_this_tick[DEFAULT_CURRENCY] = 0.0
        self.expenditure_this_tick[DEFAULT_CURRENCY] += welfare_spending

        # Retrieve tax stats from TaxService
        revenue_snapshot = self.tax_service.get_revenue_breakdown_this_tick()
        revenue_snapshot["tick"] = current_tick
        revenue_snapshot["total"] = self.tax_service.get_total_collected_this_tick()

        # WO-057 Deficit Spending: Update total_debt based on FinanceSystem
        if self.finance_system:
             self.total_debt = sum(b.face_value for b in self.finance_system.outstanding_bonds)
        else:
             # Legacy check
             current_balance = self.wallet.get_balance(DEFAULT_CURRENCY)
             if current_balance < 0:
                 self.total_debt = abs(current_balance)
             else:
                 self.total_debt = 0.0

        self.tax_history.append(revenue_snapshot)
        if len(self.tax_history) > self.history_window_size:
            self.tax_history.pop(0)

        # Retrieve local stats (Education, Stimulus are not tracked in TaxService/WelfareService aggregates yet explicitly)
        # Note: Stimulus is part of welfare_spending in WelfareService, so we might not be able to separate it easily unless we query service
        # For education, it is missing in current logic.
        # We use a simplified snapshot for now or default to 0.0 for missing parts.

        welfare_snapshot = {
            "tick": current_tick,
            "welfare": welfare_spending,
            "stimulus": 0.0, # Stimulus tracking requires Service update, keeping 0.0 for now to match current behavior
            "education": 0.0, # WO-054
            "debt": self.total_debt,
            "assets": self.assets
        }
        self.welfare_history.append(welfare_snapshot)
        if len(self.welfare_history) > self.history_window_size:
            self.welfare_history.pop(0)

    def get_monetary_delta(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> float:
        """
        Returns the net change in the money supply authorized this tick for a specific currency.
        Delegates to MonetaryLedger.
        """
        return self.monetary_ledger.get_monetary_delta(currency)

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

    def deposit(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        Deposits a given amount into the government's assets.
        Conforms to IFinancialEntity (defaults to DEFAULT_CURRENCY).
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.wallet.add(amount, currency)

    def withdraw(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        Withdraws a given amount from the government's assets.
        Conforms to IFinancialEntity (defaults to DEFAULT_CURRENCY).
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        # Wallet checks sufficiency
        self.wallet.subtract(amount, currency)

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
