from modules.government.constants import *
from _typeshed import Incomplete
from modules.common.financial.api import IFinancialAgent
from modules.finance.api import BailoutLoanDTO as BailoutLoanDTO, IPortfolioHandler as IPortfolioHandler, InsufficientFundsError as InsufficientFundsError, PortfolioDTO, TaxCollectionResult
from modules.finance.wallet.api import IWallet as IWallet
from modules.government.api import IFiscalBondService as IFiscalBondService, ITaxService as ITaxService, IWelfareService as IWelfareService
from modules.government.dtos import BailoutResultDTO as BailoutResultDTO, ExecutionResultDTO as ExecutionResultDTO, FiscalPolicyDTO as FiscalPolicyDTO, GovernmentStateDTO, PaymentRequestDTO as PaymentRequestDTO, TaxAssessmentResultDTO as TaxAssessmentResultDTO, WelfareResultDTO as WelfareResultDTO
from modules.simulation.api import AgentSensorySnapshotDTO as AgentSensorySnapshotDTO, ISensoryDataProvider
from modules.system.api import CurrencyCode as CurrencyCode, ICurrencyHolder
from simulation.agents.central_bank import CentralBank as CentralBank
from simulation.ai.enums import EconomicSchool as EconomicSchool, PolicyActionTag as PolicyActionTag, PoliticalParty as PoliticalParty
from simulation.dtos import GovernmentSensoryDTO as GovernmentSensoryDTO
from simulation.dtos.api import MarketSnapshotDTO as MarketSnapshotDTO
from simulation.dtos.strategy import ScenarioStrategy as ScenarioStrategy
from simulation.finance.api import ISettlementSystem as ISettlementSystem
from simulation.interfaces.policy_interface import IGovernmentPolicy as IGovernmentPolicy
from simulation.models import Transaction as Transaction
from simulation.policies.adaptive_gov_policy import AdaptiveGovPolicy as AdaptiveGovPolicy
from simulation.policies.smart_leviathan_policy import SmartLeviathanPolicy as SmartLeviathanPolicy
from simulation.policies.taylor_rule_policy import TaylorRulePolicy as TaylorRulePolicy
from simulation.portfolio import Portfolio as Portfolio
from simulation.systems.ministry_of_education import MinistryOfEducation as MinistryOfEducation
from typing import Any, Deque

logger: Incomplete

class Government(ICurrencyHolder, IFinancialAgent, ISensoryDataProvider):
    """
    Refactored Government Agent (Orchestrator).
    Delegates decision-making and execution to stateless engines.
    """
    id: Incomplete
    name: Incomplete
    is_active: bool
    wallet: Incomplete
    config_module: Incomplete
    settlement_system: ISettlementSystem | None
    tax_service: ITaxService
    welfare_manager: IWelfareService
    fiscal_bond_service: IFiscalBondService
    ministry_of_education: Incomplete
    infrastructure_manager: Incomplete
    monetary_ledger: Incomplete
    policy_lockout_manager: Incomplete
    public_manager: Incomplete
    fiscal_engine: Incomplete
    execution_engine: Incomplete
    fiscal_policy: FiscalPolicyDTO
    total_spent_subsidies: dict[CurrencyCode, float]
    infrastructure_level: int
    potential_gdp: float
    gdp_ema: float
    fiscal_stance: float
    policy_engine: IGovernmentPolicy
    ai: Incomplete
    ruling_party: PoliticalParty
    approval_rating: float
    public_opinion_queue: Deque[float]
    perceived_public_opinion: float
    last_election_tick: int
    income_tax_rate: float
    corporate_tax_rate: float
    welfare_budget_multiplier: float
    firm_subsidy_budget_multiplier: float
    effective_tax_rate: float
    total_debt: int
    tax_history: list[dict[str, Any]]
    welfare_history: list[dict[str, float]]
    history_window_size: int
    gdp_history: list[float]
    gdp_history_window: int
    price_history_shadow: Deque[float]
    expenditure_this_tick: dict[CurrencyCode, int]
    average_approval_rating: float
    sensory_data: GovernmentSensoryDTO | None
    finance_system: Incomplete
    last_fiscal_activation_tick: int
    portfolio: Incomplete
    def __init__(self, id: int, initial_assets: float = 0.0, config_module: Any = None, strategy: ScenarioStrategy | None = None) -> None: ...
    @property
    def state(self) -> GovernmentStateDTO: ...
    def get_sensory_snapshot(self) -> AgentSensorySnapshotDTO: ...
    @property
    def total_collected_tax(self) -> dict[CurrencyCode, int]: ...
    @property
    def revenue_this_tick(self) -> dict[CurrencyCode, int]: ...
    @property
    def tax_revenue(self) -> dict[str, float]: ...
    def get_assets_by_currency(self) -> dict[CurrencyCode, int]: ...
    def update_sensory_data(self, dto: GovernmentSensoryDTO): ...
    def calculate_income_tax(self, income: float, survival_cost: float) -> float: ...
    def calculate_corporate_tax(self, profit: float) -> float: ...
    def reset_tick_flow(self) -> None: ...
    def record_gdp(self, gdp: float) -> None: ...
    def process_monetary_transactions(self, transactions: list[Transaction]): ...
    def record_revenue(self, result: TaxCollectionResult): ...
    def make_policy_decision(self, market_data: dict[str, Any], current_tick: int, central_bank: CentralBank):
        """
        Orchestrates policy decision and execution using engines.
        """
    SCHOOL_TO_POLICY_MAP: Incomplete
    def fire_advisor(self, school: EconomicSchool, current_tick: int) -> None: ...
    def provide_household_support(self, household: Any, amount: float, current_tick: int) -> list[Transaction]:
        """
        Manually executes household support.
        DEPRECATED: Should rely on execute_social_policy via welfare manager.
        """
    def provide_firm_bailout(self, firm: Any, amount: int, current_tick: int) -> tuple[BailoutLoanDTO | None, list[Transaction]]:
        """Provides a bailout loan to a firm if it's eligible. Returns (LoanDTO, Transactions)."""
    def get_survival_cost(self, market_data: dict[str, Any]) -> float:
        """ Calculates current survival cost based on food prices. Delegates to WelfareManager. """
    def run_welfare_check(self, agents: list[Any], market_data: dict[str, Any], current_tick: int) -> list[Transaction]: ...
    def execute_social_policy(self, agents: list[Any], market_data: dict[str, Any], current_tick: int) -> list[Transaction]:
        """
        Orchestrates Tax Collection and Welfare Distribution using Execution Engine.
        """
    def invest_infrastructure(self, current_tick: int, households: list[Any] = None) -> list[Transaction]: ...
    def finalize_tick(self, current_tick: int): ...
    def get_monetary_delta(self, currency: CurrencyCode = ...) -> float: ...
    def get_agent_data(self) -> dict[str, Any]: ...
    def get_debt_to_gdp_ratio(self) -> float: ...
    def get_balance(self, currency: CurrencyCode = ...) -> int: ...
    @property
    def balance_pennies(self) -> int: ...
    def deposit(self, amount_pennies: int, currency: CurrencyCode = ...) -> None: ...
    def withdraw(self, amount_pennies: int, currency: CurrencyCode = ...) -> None: ...
    def get_all_balances(self) -> dict[CurrencyCode, int]: ...
    @property
    def total_wealth(self) -> int: ...
    def get_liquid_assets(self, currency: CurrencyCode = ...) -> int: ...
    def get_total_debt(self) -> int: ...
    def run_public_education(self, agents: list[Any], config_module: Any, current_tick: int) -> list[Transaction]: ...
    def get_portfolio(self) -> PortfolioDTO: ...
    def receive_portfolio(self, portfolio: PortfolioDTO) -> None: ...
    def clear_portfolio(self) -> None: ...
