import logging
import warnings
from typing import Dict, List, Any, Deque, Tuple, Optional, TYPE_CHECKING
from collections import deque
from simulation.ai.enums import PoliticalParty, PolicyActionTag, EconomicSchool
from simulation.interfaces.policy_interface import IGovernmentPolicy
# Keep these imports for now to avoid breaking type checks if other modules use them
from simulation.policies.taylor_rule_policy import TaylorRulePolicy
from simulation.policies.smart_leviathan_policy import SmartLeviathanPolicy
from simulation.policies.adaptive_gov_policy import AdaptiveGovPolicy

from simulation.dtos import GovernmentSensoryDTO
from simulation.dtos.api import MarketSnapshotDTO
from modules.common.utils.shadow_logger import log_shadow
from simulation.models import Transaction
from simulation.systems.ministry_of_education import MinistryOfEducation
from simulation.portfolio import Portfolio
from modules.finance.api import InsufficientFundsError, TaxCollectionResult, IPortfolioHandler, PortfolioDTO, PortfolioAsset
from modules.common.financial.api import IFinancialAgent
from modules.government.dtos import (
    FiscalPolicyDTO,
    GovernmentPolicyDTO,
    PaymentRequestDTO,
    WelfareResultDTO,
    BailoutResultDTO,
    GovernmentStateDTO,
    PolicyDecisionDTO,
    ExecutionResultDTO,
    FiscalContextDTO,
    BondIssueRequestDTO,
    TaxAssessmentResultDTO
)
from modules.government.api import (
    GovernmentExecutionContext,
    ITaxService,
    IWelfareService,
    IFiscalBondService
)
from modules.government.services.welfare_service import WelfareService
from modules.government.tax.service import TaxService
from modules.government.services.fiscal_bond_service import FiscalBondService
from modules.government.components.infrastructure_manager import InfrastructureManager
from modules.government.constants import *
from modules.government.components.monetary_ledger import MonetaryLedger
from modules.government.components.policy_lockout_manager import PolicyLockoutManager
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY, ICurrencyHolder
from modules.finance.wallet.wallet import Wallet
from modules.finance.wallet.api import IWallet
from modules.simulation.api import ISensoryDataProvider, AgentSensorySnapshotDTO

# New Engines
from modules.government.engines.execution_engine import PolicyExecutionEngine
from modules.government.engines.fiscal_engine import FiscalEngine
from modules.government.engines.api import FiscalStateDTO, FiscalRequestDTO, FirmBailoutRequestDTO, FirmFinancialsDTO

if TYPE_CHECKING:
    from simulation.finance.api import ISettlementSystem
    from modules.finance.api import BailoutLoanDTO
    from simulation.dtos.strategy import ScenarioStrategy
    from simulation.agents.central_bank import CentralBank

logger = logging.getLogger(__name__)

class Government(ICurrencyHolder, IFinancialAgent, ISensoryDataProvider):
    """
    Refactored Government Agent (Orchestrator).
    Delegates decision-making and execution to stateless engines.
    """

    def __init__(self, id: int, initial_assets: float = 0.0, config_module: Any = None, strategy: Optional["ScenarioStrategy"] = None):
        self.id = id

        initial_balance_dict = {}
        if isinstance(initial_assets, dict):
            # MIGRATION: Convert dict values to int if needed, assuming input might still be floats from config
            for k, v in initial_assets.items():
                initial_balance_dict[k] = int(v)
        else:
            initial_balance_dict[DEFAULT_CURRENCY] = int(initial_assets)

        self.wallet = Wallet(self.id, initial_balance_dict)

        self.config_module = config_module
        self.settlement_system: Optional["ISettlementSystem"] = None
        
        # Services
        self.tax_service: ITaxService = TaxService(config_module)
        self.welfare_manager: IWelfareService = WelfareService(config_module) # Kept name for context compat
        self.fiscal_bond_service: IFiscalBondService = FiscalBondService(config_module)

        self.ministry_of_education = MinistryOfEducation(config_module)
        self.infrastructure_manager = InfrastructureManager(self)
        self.monetary_ledger = MonetaryLedger()
        self.policy_lockout_manager = PolicyLockoutManager()
        self.public_manager = None # Will be injected by Initializer

        # Initialize engines
        policy_mode = getattr(config_module, "GOVERNMENT_POLICY_MODE", "TAYLOR_RULE")
        self.fiscal_engine = FiscalEngine(config_module)
        self.execution_engine = PolicyExecutionEngine()

        # Initialize default fiscal policy
        self.fiscal_policy: FiscalPolicyDTO = self.tax_service.determine_fiscal_stance(
            MarketSnapshotDTO(tick=0, market_signals={}, market_data={})
        )

        # Legacy State Attributes
        self.total_spent_subsidies: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.infrastructure_level: int = 0
        self.potential_gdp: float = 0.0
        self.gdp_ema: float = 0.0
        self.fiscal_stance: float = 0.0

        # Legacy Policy Engine
        if policy_mode == "AI_ADAPTIVE":
            self.policy_engine: IGovernmentPolicy = AdaptiveGovPolicy(self, config_module)
        elif policy_mode == "AI_LEGACY":
            self.policy_engine: IGovernmentPolicy = SmartLeviathanPolicy(self, config_module)
        else:
            self.policy_engine: IGovernmentPolicy = TaylorRulePolicy(config_module)
        self.ai = getattr(self.policy_engine, "ai", None)

        self.ruling_party: PoliticalParty = PoliticalParty.BLUE
        self.approval_rating: float = 0.5
        self.public_opinion_queue: Deque[float] = deque(maxlen=4)
        self.perceived_public_opinion: float = 0.5
        self.last_election_tick: int = 0

        self.income_tax_rate: float = getattr(config_module, "INCOME_TAX_RATE", 0.1)
        self.corporate_tax_rate: float = getattr(config_module, "CORPORATE_TAX_RATE", 0.2)

        if strategy:
             if strategy.initial_income_tax_rate is not None:
                 self.income_tax_rate = strategy.initial_income_tax_rate
             if strategy.initial_corporate_tax_rate is not None:
                 self.corporate_tax_rate = strategy.initial_corporate_tax_rate

        if strategy and strategy.is_active:
             if strategy.fiscal_shock_tax_rate is not None:
                 self.corporate_tax_rate = strategy.fiscal_shock_tax_rate
             if strategy.corporate_tax_rate_delta is not None:
                 self.corporate_tax_rate += strategy.corporate_tax_rate_delta

        self.welfare_budget_multiplier: float = 1.0
        self.firm_subsidy_budget_multiplier: float = 1.0
        self.effective_tax_rate: float = self.income_tax_rate
        self.total_debt: int = 0

        # History buffers
        self.tax_history: List[Dict[str, Any]] = []
        self.welfare_history: List[Dict[str, float]] = []
        self.history_window_size = 5000
        self.gdp_history: List[float] = []
        self.gdp_history_window = 20
        
        ticks_per_year = int(getattr(config_module, "TICKS_PER_YEAR", DEFAULT_TICKS_PER_YEAR))
        self.price_history_shadow: Deque[float] = deque(maxlen=ticks_per_year)
        self.expenditure_this_tick: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}
        self.average_approval_rating = 0.5

        self.sensory_data: Optional[GovernmentSensoryDTO] = None
        self.finance_system = None
        self.last_fiscal_activation_tick: int = -1
        self.portfolio = Portfolio(self.id)

        logger.info(
            f"Government {self.id} initialized with assets: {self.wallet.get_all_balances()}",
            extra={"tick": 0, "agent_id": self.id, "tags": ["init", "government"]},
        )

    def get_sensory_snapshot(self) -> AgentSensorySnapshotDTO:
        return {
            "is_active": True,
            "approval_rating": self.approval_rating,
            "total_wealth": self.total_wealth # int
        }

    @property
    def total_collected_tax(self) -> Dict[CurrencyCode, float]:
        # Legacy compat, ideally int. TaxService might still return float.
        return self.tax_service.get_total_collected_tax()

    @property
    def revenue_this_tick(self) -> Dict[CurrencyCode, float]:
        return self.tax_service.get_revenue_this_tick()

    @property
    def tax_revenue(self) -> Dict[str, float]:
        return self.tax_service.get_tax_revenue()

    def get_assets_by_currency(self) -> Dict[CurrencyCode, int]:
        return self.wallet.get_all_balances()

    def _internal_add_assets(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.wallet.add(int(amount), currency, memo="Internal Add")

    def _internal_sub_assets(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.wallet.subtract(int(amount), currency, memo="Internal Sub")

    def update_sensory_data(self, dto: GovernmentSensoryDTO):
        self.sensory_data = dto
        if dto.tick % 50 == 0:
            inf_sma = dto.inflation_sma if isinstance(dto.inflation_sma, (int, float)) else 0.0
            app_sma = dto.approval_sma if isinstance(dto.approval_sma, (int, float)) else 0.0
            logger.debug(
                f"SENSORY_UPDATE | Government received macro data. Inflation_SMA: {inf_sma:.4f}, Approval_SMA: {app_sma:.2f}",
                extra={"tick": dto.tick, "agent_id": self.id, "tags": ["sensory", "wo-057-b"]}
            )

    def calculate_income_tax(self, income: float, survival_cost: float) -> float:
        return self.tax_service.calculate_tax_liability(self.fiscal_policy, income)

    def calculate_corporate_tax(self, profit: float) -> float:
        return self.tax_service.calculate_corporate_tax(profit, self.corporate_tax_rate)

    def reset_tick_flow(self):
        self.tax_service.reset_tick_flow()
        self.welfare_manager.reset_tick_flow()
        self.monetary_ledger.reset_tick_flow()
        self.expenditure_this_tick = {DEFAULT_CURRENCY: 0}

    def record_gdp(self, gdp: float) -> None:
        self.gdp_history.append(gdp)
        if len(self.gdp_history) > self.gdp_history_window:
            self.gdp_history.pop(0)

    def process_monetary_transactions(self, transactions: List[Transaction]):
        self.monetary_ledger.process_transactions(transactions)

    def record_revenue(self, result: "TaxCollectionResult"):
        self.tax_service.record_revenue(result)

    # --- Refactored: Make Policy Decision ---
    def make_policy_decision(self, market_data: Dict[str, Any], current_tick: int, central_bank: "CentralBank"):
        """
        Orchestrates policy decision and execution using engines.
        """
        # 0. Update Fiscal Policy (Legacy compat)
        if getattr(self.config_module, "ENABLE_FISCAL_STABILIZER", True):
            snapshot = MarketSnapshotDTO(
                tick=current_tick,
                market_signals={},
                market_data=market_data
            )
            from dataclasses import replace
            policy = self.tax_service.determine_fiscal_stance(snapshot)
            self.fiscal_policy = replace(
                policy,
                corporate_tax_rate=self.corporate_tax_rate,
                income_tax_rate=self.income_tax_rate,
                welfare_budget_multiplier=self.welfare_budget_multiplier
            )

        # 0.5. Execute Policy Engine (AI/Legacy)
        # Allows AI to override parameters before FiscalEngine calculation or as parallel decision.
        if self.policy_engine:
             # Pass required arguments for SmartLeviathanPolicy (and ensure others handle it or use kwargs)
             # IGovernmentPolicy signature usually requires more context.
             try:
                 # Attempt to call with SmartLeviathan signature (requires government instance)
                 # Note: SmartLeviathanPolicy.decide(government, sensory_data, tick, cb)
                 decision_legacy = self.policy_engine.decide(
                     self,
                     self.sensory_data,
                     current_tick,
                     central_bank
                 )
             except TypeError:
                 # Fallback for policies with simpler signature (Legacy/TaylorRule: decide(market_data))
                 decision_legacy = self.policy_engine.decide(market_data)

             if decision_legacy and isinstance(decision_legacy, dict):
                 self._apply_state_updates(decision_legacy)

        # Update Potential GDP (Agent Logic)
        current_gdp = market_data.get("total_production", 0.0)
        if current_gdp == 0.0 and self.sensory_data:
             current_gdp = self.sensory_data.current_gdp

        if self.potential_gdp == 0.0:
            self.potential_gdp = current_gdp
        else:
            alpha = 0.01
            self.potential_gdp = (alpha * current_gdp) + ((1-alpha) * self.potential_gdp)

        # 1. Gather State into DTO
        fiscal_state = FiscalStateDTO(
            tick=current_tick,
            assets=self.wallet.get_all_balances(),
            total_debt=self.total_debt,
            income_tax_rate=self.income_tax_rate,
            corporate_tax_rate=self.corporate_tax_rate,
            approval_rating=self.approval_rating,
            welfare_budget_multiplier=self.welfare_budget_multiplier,
            potential_gdp=self.potential_gdp
        )

        # Prepare Market Snapshot DTO (Dataclass for Engines)
        engine_market_snapshot = MarketSnapshotDTO(
            tick=current_tick,
            market_signals={},
            market_data={"current_gdp": current_gdp}
        )

        # 2. Call Fiscal Engine
        decision = self.fiscal_engine.decide(fiscal_state, engine_market_snapshot, [])

        # 3. Apply Changes
        if decision.new_income_tax_rate is not None:
            self.income_tax_rate = decision.new_income_tax_rate
        if decision.new_corporate_tax_rate is not None:
            self.corporate_tax_rate = decision.new_corporate_tax_rate
        if decision.new_welfare_budget_multiplier is not None:
            self.welfare_budget_multiplier = decision.new_welfare_budget_multiplier

        logger.debug(
            f"FISCAL_POLICY_EXECUTED | Tick: {current_tick} | IncomeTax: {self.income_tax_rate:.2f} | CorpTax: {self.corporate_tax_rate:.2f}",
            extra={"tick": current_tick, "agent_id": self.id}
        )

        # Legacy Shadow Logging
        self._log_shadow_metrics(market_data, current_tick, central_bank)

    def _apply_state_updates(self, updates: Dict[str, Any]):
        if "income_tax_rate" in updates:
            self.income_tax_rate = updates["income_tax_rate"]
        if "corporate_tax_rate" in updates:
            self.corporate_tax_rate = updates["corporate_tax_rate"]
        if "welfare_budget_multiplier" in updates:
            self.welfare_budget_multiplier = updates["welfare_budget_multiplier"]
        if "potential_gdp" in updates:
            self.potential_gdp = updates["potential_gdp"]
        if "fiscal_stance" in updates:
            self.fiscal_stance = updates["fiscal_stance"]

    def _log_shadow_metrics(self, market_data: Dict[str, Any], current_tick: int, central_bank: Any):
        if self.potential_gdp == 0.0 and self.sensory_data and self.sensory_data.current_gdp > 0:
             self.potential_gdp = self.sensory_data.current_gdp

        inflation = 0.0
        if self.sensory_data:
            inflation = self.sensory_data.inflation_sma

        real_gdp_growth = 0.0
        if self.sensory_data:
            real_gdp_growth = self.sensory_data.gdp_growth_sma

        target_inflation = getattr(self.config_module, "CB_INFLATION_TARGET", 0.02)
        neutral_rate = max(0.01, real_gdp_growth)

        gdp_gap = 0.0
        if self.potential_gdp > 0:
             current_gdp = market_data.get("total_production", 0.0)
             gdp_gap = (current_gdp - self.potential_gdp) / self.potential_gdp

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

    SCHOOL_TO_POLICY_MAP = {
        EconomicSchool.KEYNESIAN: [PolicyActionTag.KEYNESIAN_FISCAL],
        EconomicSchool.AUSTRIAN: [PolicyActionTag.AUSTRIAN_AUSTERITY],
        EconomicSchool.MONETARIST: [PolicyActionTag.MONETARIST_RULES],
    }

    def fire_advisor(self, school: EconomicSchool, current_tick: int) -> None:
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

    def _issue_deficit_bonds(self, amount: int, current_tick: int) -> bool:
        """Helper to issue bonds for deficit spending."""
        if amount <= 0 or not self.finance_system:
            return False

        # Gather context
        current_gdp = 1000000 # Default 1M pennies
        if self.sensory_data and self.sensory_data.current_gdp > 0:
             current_gdp = int(self.sensory_data.current_gdp * 100) # Convert to pennies if float

        context = FiscalContextDTO(
            tick=current_tick,
            current_gdp=current_gdp,
            debt_to_gdp_ratio=self.get_debt_to_gdp_ratio(),
            population_count=100, # Mock
            treasury_balance=self.wallet.get_balance(DEFAULT_CURRENCY)
        )

        request = BondIssueRequestDTO(
            amount_pennies=amount,
            maturity_ticks=400,
            target_yield=0.0
        )

        buyer_pool = {}
        if hasattr(self.finance_system, 'bank'): buyer_pool['bank'] = self.finance_system.bank
        if hasattr(self.finance_system, 'central_bank'): buyer_pool['central_bank'] = self.finance_system.central_bank

        result = self.fiscal_bond_service.issue_bonds(request, context, buyer_pool)

        if result.payment_request.payer != "UNKNOWN_BUYER":
             success = self.settlement_system.transfer(
                 result.payment_request.payer,
                 self,
                 result.payment_request.amount,
                 result.payment_request.memo,
                 result.payment_request.currency
             )
             if success:
                 payer_id = result.payment_request.payer
                 if hasattr(payer_id, 'id'): payer_id = payer_id.id
                 self.finance_system.register_bond(result.bond_dto, owner_id=payer_id)
                 return True
        return False

    def provide_household_support(self, household: Any, amount: float, current_tick: int) -> List[Transaction]:
        """
        Manually executes household support.
        DEPRECATED: Should rely on execute_social_policy via welfare manager.
        """
        if self.policy_lockout_manager.is_locked(PolicyActionTag.KEYNESIAN_FISCAL, current_tick):
            return []

        effective_amount = int(amount * self.welfare_budget_multiplier)
        if effective_amount <= 0:
            return []

        current_balance = self.wallet.get_balance(DEFAULT_CURRENCY)
        if current_balance < effective_amount:
             self._issue_deficit_bonds(effective_amount - current_balance, current_tick)

        # Check balance again
        current_balance = self.wallet.get_balance(DEFAULT_CURRENCY)
        if current_balance < effective_amount:
             logger.warning(f"WELFARE_FAILED | Insufficient funds even after bond issuance attempt. Needed: {effective_amount}, Has: {current_balance}")
             return []

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
             , total_pennies=int(effective_amount * 1.0 * 100))]
        return []

    def provide_firm_bailout(self, firm: Any, amount: int, current_tick: int) -> Tuple[Optional["BailoutLoanDTO"], List[Transaction]]:
        """Provides a bailout loan to a firm if it's eligible. Returns (LoanDTO, Transactions)."""

        # 1. Create Request DTO
        is_solvent = False
        if self.finance_system:
             is_solvent = self.finance_system.evaluate_solvency(firm, current_tick)

        financials = FirmFinancialsDTO(
            assets=int(firm.total_wealth) if hasattr(firm, 'total_wealth') else (int(firm.assets) if hasattr(firm, 'assets') else 0),
            profit=0.0,
            is_solvent=is_solvent
        )

        bailout_req = FirmBailoutRequestDTO(
            firm_id=firm.id,
            requested_amount=int(amount),
            firm_financials=financials
        )

        request = FiscalRequestDTO(bailout_request=bailout_req)

        # 2. Call Engine
        fiscal_state = FiscalStateDTO(
            tick=current_tick,
            assets=self.wallet.get_all_balances(),
            total_debt=self.total_debt,
            income_tax_rate=self.income_tax_rate,
            corporate_tax_rate=self.corporate_tax_rate,
            approval_rating=self.approval_rating,
            welfare_budget_multiplier=self.welfare_budget_multiplier,
            potential_gdp=self.potential_gdp
        )
        market_snapshot = MarketSnapshotDTO(
            tick=current_tick,
            market_signals={},
            market_data={
                "inflation_rate_annual": 0.0,
                "current_gdp": 0.0
            }
        )

        decision = self.fiscal_engine.decide(fiscal_state, market_snapshot, [request])

        # 3. Execute Decision
        if decision.bailouts_to_grant:
            grant = decision.bailouts_to_grant[0]

            if self.finance_system:
                loan, txs = self.finance_system.grant_bailout_loan(firm, grant.amount, current_tick)

                cur = DEFAULT_CURRENCY
                if cur not in self.expenditure_this_tick: self.expenditure_this_tick[cur] = 0
                self.expenditure_this_tick[cur] += grant.amount

                return loan, txs

        return None, []

    def get_survival_cost(self, market_data: Dict[str, Any]) -> float:
        """ Calculates current survival cost based on food prices. Delegates to WelfareManager. """
        snapshot = MarketSnapshotDTO(tick=0, market_signals={}, market_data=market_data)
        return self.welfare_manager.get_survival_cost(snapshot)

    def run_welfare_check(self, agents: List[Any], market_data: Dict[str, Any], current_tick: int) -> List[Transaction]:
        self.execute_social_policy(agents, market_data, current_tick)
        return []

    def execute_social_policy(self, agents: List[Any], market_data: Dict[str, Any], current_tick: int) -> None:
        """
        Orchestrates Tax Collection and Welfare Distribution using Execution Engine.
        """
        decision = PolicyDecisionDTO(
            action_tag=PolicyActionTag.SOCIAL_POLICY,
            parameters={},
            status="EXECUTED"
        )

        state_dto = self._get_state_dto(current_tick)
        context = self._get_execution_context()

        result = self.execution_engine.execute(
            decision,
            state_dto,
            agents,
            market_data,
            context
        )

        # Funding for Welfare
        welfare_reqs = [req for req in result.payment_requests if req.payer == self.id or (hasattr(req.payer, 'id') and req.payer.id == self.id)]
        total_welfare_needed = sum(req.amount for req in welfare_reqs)

        if total_welfare_needed > 0:
            current_balance = self.wallet.get_balance(DEFAULT_CURRENCY)
            if current_balance < total_welfare_needed:
                self._issue_deficit_bonds(total_welfare_needed - current_balance, current_tick)

        # Execute Transfers
        for req in result.payment_requests:
            payer = req.payer
            payee = req.payee

            if payer == self.id: payer = self
            if isinstance(payer, str) and "GOVERNMENT" in payer:
                payer = self

            if isinstance(payee, str) and "GOVERNMENT" in payee:
                payee = self
            elif hasattr(payee, 'id') and payee.id == self.id:
                payee = self
            elif payee == self.id:
                payee = self

            if self.settlement_system:
                success = self.settlement_system.transfer(payer, payee, int(req.amount), req.memo, currency=req.currency)

                if success:
                    if payee == self: # Tax
                         self.record_revenue(TaxCollectionResult(
                             success=True,
                             amount_collected=int(req.amount),
                             tax_type=req.memo if req.memo else "wealth_tax",
                             payer_id=payer.id if hasattr(payer, 'id') else payer,
                             payee_id=self.id,
                             error_message=None
                         ))

    def invest_infrastructure(self, current_tick: int, households: List[Any] = None) -> List[Transaction]:
        return self.infrastructure_manager.invest_infrastructure(current_tick, households)

    def finalize_tick(self, current_tick: int):
        welfare_spending = self.welfare_manager.get_spending_this_tick()

        if DEFAULT_CURRENCY not in self.expenditure_this_tick:
            self.expenditure_this_tick[DEFAULT_CURRENCY] = 0
        self.expenditure_this_tick[DEFAULT_CURRENCY] += int(welfare_spending)

        revenue_snapshot = self.tax_service.get_revenue_breakdown_this_tick()
        revenue_snapshot["tick"] = current_tick
        revenue_snapshot["total"] = self.tax_service.get_total_collected_this_tick()

        if self.finance_system:
             self.total_debt = sum(b.face_value for b in self.finance_system.outstanding_bonds)
        else:
             current_balance = self.wallet.get_balance(DEFAULT_CURRENCY)
             if current_balance < 0:
                 self.total_debt = abs(current_balance)
             else:
                 self.total_debt = 0

        self.tax_history.append(revenue_snapshot)
        if len(self.tax_history) > self.history_window_size:
            self.tax_history.pop(0)

        welfare_snapshot = {
            "tick": current_tick,
            "welfare": welfare_spending,
            "stimulus": 0.0,
            "education": 0.0,
            "debt": self.total_debt,
            "assets": self.total_wealth
        }
        self.welfare_history.append(welfare_snapshot)
        if len(self.welfare_history) > self.history_window_size:
            self.welfare_history.pop(0)

    def get_monetary_delta(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> float:
        return self.monetary_ledger.get_monetary_delta(currency)

    def get_agent_data(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_type": "government",
            "assets": self.total_wealth,
            "ruling_party": self.ruling_party.name,
            "approval_rating": self.approval_rating,
            "income_tax_rate": self.income_tax_rate,
            "corporate_tax_rate": self.corporate_tax_rate,
            "perceived_public_opinion": self.perceived_public_opinion
        }

    def get_debt_to_gdp_ratio(self) -> float:
        if not self.sensory_data or self.sensory_data.current_gdp == 0:
            return 0.0
        debt = max(0.0, float(self.total_debt)) # Use total_debt instead of negative wealth
        return debt / self.sensory_data.current_gdp

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self.wallet.get_balance(currency)

    @property
    def balance_pennies(self) -> int:
        return self.wallet.get_balance(DEFAULT_CURRENCY)

    def deposit(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._deposit(amount_pennies, currency)

    def withdraw(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._withdraw(amount_pennies, currency)

    # --- IFinancialAgent Implementation ---
    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.wallet.add(amount, currency, memo="Deposit")

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.wallet.subtract(amount, currency, memo="Withdraw")

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        return self.wallet.get_all_balances()

    @property
    def total_wealth(self) -> int:
        return self.wallet.get_balance(DEFAULT_CURRENCY)

    def get_liquid_assets(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self.wallet.get_balance(currency)

    def get_total_debt(self) -> int:
        return self.total_debt

    def run_public_education(self, agents: List[Any], config_module: Any, current_tick: int) -> List[Transaction]:
        households = [a for a in agents if hasattr(a, '_econ_state')]
        return self.ministry_of_education.run_public_education(households, self, current_tick)

    # --- IPortfolioHandler Implementation ---
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
        for asset in portfolio.assets:
            if asset.asset_type == "stock":
                try:
                    firm_id = int(asset.asset_id)
                    self.portfolio.add(firm_id, asset.quantity, 0.0)
                except ValueError:
                    logger.error(f"Invalid firm_id in portfolio receive: {asset.asset_id}")
            else:
                logger.warning(f"Government received unhandled asset type: {asset.asset_type} (ID: {asset.asset_id})")

    def clear_portfolio(self) -> None:
        self.portfolio.holdings.clear()

    # --- Helpers ---
    def _get_state_dto(self, tick: int) -> GovernmentStateDTO:
        # Construct GovernmentPolicyDTO from fiscal_policy
        policy_dto = GovernmentPolicyDTO(
            tax_brackets=self.fiscal_policy.tax_brackets,
            income_tax_rate=self.fiscal_policy.income_tax_rate,
            corporate_tax_rate=self.fiscal_policy.corporate_tax_rate,
            vat_rate=self.fiscal_policy.vat_rate,
            # Monetary Policy (defaults or from elsewhere?)
            target_interest_rate=0.05,
            inflation_target=0.02,
            unemployment_target=0.05,
            welfare_budget_multiplier=self.welfare_budget_multiplier,
            bailout_threshold_solvency=0.1
        )

        return GovernmentStateDTO(
            tick=tick,
            assets=self.wallet.get_all_balances(),
            total_debt=self.total_debt,
            income_tax_rate=self.income_tax_rate,
            corporate_tax_rate=self.corporate_tax_rate,
            policy=self.fiscal_policy,
            ruling_party=self.ruling_party,
            approval_rating=self.approval_rating,
            policy_lockouts=self.policy_lockout_manager._lockouts,
            sensory_data=self.sensory_data,
            gdp_history=list(self.gdp_history),
            potential_gdp=self.potential_gdp,
            fiscal_stance=self.fiscal_stance
        )

    def _get_execution_context(self) -> GovernmentExecutionContext:
        return GovernmentExecutionContext(
            settlement_system=self.settlement_system,
            finance_system=self.finance_system,
            tax_service=self.tax_service,
            welfare_manager=self.welfare_manager,
            fiscal_bond_service=self.fiscal_bond_service,
            infrastructure_manager=self.infrastructure_manager,
            public_manager=self.public_manager
        )
