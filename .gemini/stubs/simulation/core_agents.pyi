from _typeshed import Incomplete
from logging import Logger as Logger
from modules.analytics.dtos import AgentTickAnalyticsDTO
from modules.common.financial.api import IFinancialAgent as IFinancialAgent, IFinancialEntity
from modules.common.interfaces import IInvestor, IPropertyOwner as IPropertyOwner
from modules.finance.api import ICreditFrozen
from modules.government.political.api import IVoter, VoteRecordDTO
from modules.household.api import BudgetPlan as BudgetPlan, CloningRequestDTO as CloningRequestDTO, HousingActionDTO as HousingActionDTO, PrioritizedNeed as PrioritizedNeed
from modules.household.dtos import EconContextDTO as EconContextDTO, HouseholdSnapshotDTO, HouseholdStateDTO
from modules.household.mixins._state_access import HouseholdStateAccessMixin
from modules.household.services import HouseholdSnapshotAssembler as HouseholdSnapshotAssembler
from modules.hr.api import IEmployeeDataProvider
from modules.market.api import IHousingTransactionParticipant
from modules.simulation.api import AgentCoreConfigDTO as AgentCoreConfigDTO, AgentSensorySnapshotDTO as AgentSensorySnapshotDTO, AgentStateDTO, IDecisionEngine as IDecisionEngine, IEducated, IInventoryHandler, IOrchestratorAgent, ISensoryDataProvider, InventorySlot
from modules.simulation.dtos.api import HouseholdConfigDTO as HouseholdConfigDTO
from modules.system.api import CurrencyCode as CurrencyCode
from simulation.ai.api import Aggressiveness as Aggressiveness, Personality as Personality, Tactic as Tactic
from simulation.ai.household_ai import HouseholdAI as HouseholdAI
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine as AIDrivenHouseholdDecisionEngine
from simulation.decisions.base_decision_engine import BaseDecisionEngine as BaseDecisionEngine
from simulation.dtos import ConsumptionResult as ConsumptionResult, DecisionContext as DecisionContext, DecisionInputDTO as DecisionInputDTO, FiscalContext as FiscalContext, LeisureEffectDTO as LeisureEffectDTO, MacroFinancialContext as MacroFinancialContext
from simulation.dtos.household_state_container import HouseholdStateContainer as HouseholdStateContainer
from simulation.dtos.scenario import StressScenarioConfig as StressScenarioConfig
from simulation.loan_market import LoanMarket as LoanMarket
from simulation.models import Order as Order, Skill as Skill, Talent as Talent
from simulation.portfolio import Portfolio as Portfolio
from simulation.systems.api import ILearningAgent as ILearningAgent, LearningUpdateContext as LearningUpdateContext, LifecycleContext as LifecycleContext, MarketInteractionContext as MarketInteractionContext
from typing import Any
from typing_extensions import override

logger: Incomplete

class Household(ILearningAgent, IEmployeeDataProvider, IEducated, IHousingTransactionParticipant, IFinancialEntity, IOrchestratorAgent, ICreditFrozen, IInventoryHandler, ISensoryDataProvider, IInvestor, HouseholdStateAccessMixin, IVoter):
    """
    Household Agent (Orchestrator).
    Delegates Bio/Econ/Social logic to specialized stateless Engines.
    State is held in internal DTOs.
    """
    config: Incomplete
    logger: Incomplete
    demographic_manager: Incomplete
    last_labor_allocation: float
    lifecycle_engine: Incomplete
    needs_engine: Incomplete
    social_engine: Incomplete
    budget_engine: Incomplete
    consumption_engine: Incomplete
    belief_engine: Incomplete
    crisis_engine: Incomplete
    housing_connector: Incomplete
    decision_engine: Incomplete
    id: Incomplete
    name: Incomplete
    memory_v2: Incomplete
    value_orientation: Incomplete
    needs: Incomplete
    preference_asset: Incomplete
    preference_social: Incomplete
    preference_growth: Incomplete
    goods_info_map: Incomplete
    goods_data: Incomplete
    risk_aversion: Incomplete
    distress_tick_counter: int
    def __init__(self, core_config: AgentCoreConfigDTO, engine: IDecisionEngine, talent: Talent, goods_data: list[dict[str, Any]], personality: Personality, config_dto: HouseholdConfigDTO, loan_market: LoanMarket | None = None, risk_aversion: float = 1.0, initial_age: float | None = None, gender: str | None = None, parent_id: int | None = None, generation: int | None = None, initial_assets_record: int | None = None, demographic_manager: Any | None = None, major: str | None = None, **kwargs) -> None: ...
    @property
    def state(self) -> HouseholdStateContainer: ...
    def get_core_config(self) -> AgentCoreConfigDTO: ...
    def get_sensory_snapshot(self) -> AgentSensorySnapshotDTO: ...
    def get_current_state(self) -> AgentStateDTO: ...
    def load_state(self, state: AgentStateDTO) -> None: ...
    @property
    def is_active(self) -> bool: ...
    @is_active.setter
    def is_active(self, value: bool): ...
    @property
    def gender(self) -> str: ...
    @property
    def parent_id(self) -> int | None: ...
    @property
    def generation(self) -> int: ...
    @property
    def age(self) -> float: ...
    @age.setter
    def age(self, value: float) -> None: ...
    @property
    def sex(self) -> str:
        """Biological sex (M/F). Used for reproduction and matching (Wave 4)."""
    @property
    def health_status(self) -> float:
        """Normalized health (0.0 to 1.0). (Wave 4)"""
    @health_status.setter
    def health_status(self, value: float) -> None: ...
    @property
    def has_disease(self) -> bool:
        """Infection status requiring medical utility. (Wave 4)"""
    @has_disease.setter
    def has_disease(self, value: bool) -> None: ...
    @property
    def spouse_id(self) -> int | None: ...
    @spouse_id.setter
    def spouse_id(self, value: int | None) -> None: ...
    @property
    def children_ids(self) -> list[int]: ...
    def add_child(self, child_id: int) -> None:
        """Adds a child to the household's bio state."""
    @property
    def social_status(self) -> float: ...
    @social_status.setter
    def social_status(self, value: float) -> None: ...
    @property
    def social_rank(self) -> float: ...
    @social_rank.setter
    def social_rank(self, value: float) -> None: ...
    @property
    def conformity(self) -> float: ...
    @conformity.setter
    def conformity(self, value: float) -> None: ...
    @property
    def is_employed(self) -> bool: ...
    @is_employed.setter
    def is_employed(self, value: bool) -> None: ...
    @property
    def employer_id(self) -> int | None: ...
    @employer_id.setter
    def employer_id(self, value: int | None) -> None: ...
    @property
    def labor_skill(self) -> float: ...
    @labor_skill.setter
    def labor_skill(self, value: float) -> None: ...
    @property
    def inventory(self) -> dict[str, float]: ...
    @property
    def portfolio(self) -> Portfolio: ...
    @property
    def talent(self) -> Talent: ...
    @property
    def labor_income_this_tick(self) -> int: ...
    @labor_income_this_tick.setter
    def labor_income_this_tick(self, value: int) -> None: ...
    @property
    def capital_income_this_tick(self) -> int: ...
    @capital_income_this_tick.setter
    def capital_income_this_tick(self, value: int) -> None: ...
    @property
    def employment_start_tick(self) -> int: ...
    @employment_start_tick.setter
    def employment_start_tick(self, value: int) -> None: ...
    def quit(self) -> None:
        """
        Executes the resignation process for the employee.
        Sets is_employed to False and clears employer_id.
        """
    @property
    def tick_analytics(self) -> AgentTickAnalyticsDTO: ...
    @property
    def personality(self) -> Personality: ...
    @property
    def education_xp(self) -> float: ...
    @education_xp.setter
    def education_xp(self, value: float) -> None: ...
    @property
    def education_level(self) -> int: ...
    @education_level.setter
    def education_level(self, value: int) -> None: ...
    @property
    def expected_wage(self) -> int: ...
    @expected_wage.setter
    def expected_wage(self, value: int) -> None: ...
    def update_needs(self, current_tick: int, market_data: dict[str, Any] | None = None):
        """
        Orchestrates Lifecycle, Needs, and Social Engines.
        Called by LifecycleManager.
        """
    @override
    def make_decision(self, input_dto: DecisionInputDTO) -> tuple[list['Order'], tuple['Tactic', 'Aggressiveness']]: ...
    @property
    def owned_properties(self) -> list[int]: ...
    def add_property(self, property_id: int) -> None: ...
    def remove_property(self, property_id: int) -> None: ...
    @property
    def residing_property_id(self) -> int | None: ...
    @residing_property_id.setter
    def residing_property_id(self, value: int | None) -> None: ...
    @property
    def is_homeless(self) -> bool: ...
    @is_homeless.setter
    def is_homeless(self, value: bool) -> None: ...
    @property
    def home_quality_score(self) -> float: ...
    @home_quality_score.setter
    def home_quality_score(self, value: float) -> None: ...
    @property
    def current_wage(self) -> int: ...
    @current_wage.setter
    def current_wage(self, value: int) -> None: ...
    @property
    def credit_frozen_until_tick(self) -> int: ...
    @credit_frozen_until_tick.setter
    def credit_frozen_until_tick(self, value: int) -> None: ...
    @property
    @override
    def assets(self) -> int: ...
    @property
    def balance_pennies(self) -> int: ...
    @override
    def deposit(self, amount_pennies: int, currency: CurrencyCode = ...) -> None: ...
    @override
    def withdraw(self, amount_pennies: int, currency: CurrencyCode = ...) -> None: ...
    @property
    def balance_pennies(self) -> int:
        """Returns the balance in the default currency (pennies)."""
    @override
    def get_balance(self, currency: CurrencyCode = ...) -> int: ...
    def get_liquid_assets(self, currency: CurrencyCode = 'USD') -> int:
        """Returns liquid assets in pennies (int)."""
    def get_total_debt(self) -> int:
        """Returns total debt in pennies (int)."""
    @override
    def get_all_balances(self) -> dict[CurrencyCode, int]:
        """Returns a copy of all currency balances."""
    @property
    def total_wealth(self) -> int:
        """
        Returns the total wealth in default currency estimation.
        TD-270: Standardized multi-currency summation.
        """
    @override
    def get_assets_by_currency(self) -> dict[CurrencyCode, int]: ...
    @override
    def add_item(self, item_id: str, quantity: float, transaction_id: str | None = None, quality: float = 1.0, slot: InventorySlot = ...) -> bool: ...
    @override
    def remove_item(self, item_id: str, quantity: float, transaction_id: str | None = None, slot: InventorySlot = ...) -> bool: ...
    @override
    def get_quantity(self, item_id: str, slot: InventorySlot = ...) -> float: ...
    @override
    def get_quality(self, item_id: str, slot: InventorySlot = ...) -> float: ...
    @override
    def get_all_items(self, slot: InventorySlot = ...) -> dict[str, float]: ...
    @override
    def clear_inventory(self, slot: InventorySlot = ...) -> None: ...
    @override
    def get_agent_data(self) -> dict[str, Any]: ...
    def get_pre_state_data(self) -> dict[str, Any]: ...
    def update_pre_state_data(self) -> None: ...
    def update_learning(self, context: LearningUpdateContext) -> None: ...
    def create_snapshot_dto(self) -> HouseholdSnapshotDTO: ...
    def create_state_dto(self) -> HouseholdStateDTO:
        """Legacy DTO creation."""
    def initialize_demographics(self, age: float, gender: str, parent_id: int | None, generation: int, spouse_id: int | None = None) -> None:
        """
        Explicitly initializes demographic state.
        Used by DemographicManager during agent creation.
        """
    def initialize_personality(self, personality: Personality, desire_weights: dict[str, float]) -> None:
        """
        Explicitly initializes personality and desire weights.
        Used by DemographicManager and AITrainingManager (during brain inheritance).
        """
    def add_education_xp(self, xp: float) -> None: ...
    def add_durable_asset(self, asset: dict[str, Any]) -> None: ...
    def update_perceived_prices(self, market_data: dict[str, Any], stress_scenario_config: StressScenarioConfig | None = None, current_tick: int = 0) -> None:
        """
        Delegates to BeliefEngine for updating price beliefs.
        """
    def apply_leisure_effect(self, leisure_hours: float, consumed_items: dict[str, float]) -> LeisureEffectDTO: ...
    def consume(self, item_id: str, amount: float, current_tick: int) -> None:
        """
        Consumes an item from inventory and updates consumption stats.
        Restored legacy method used by CommerceSystem.
        """
    def record_consumption(self, amount: float, is_food: bool = False) -> None:
        """Records consumption statistics (called by Registry/Handlers)."""
    def add_labor_income(self, amount: int) -> None:
        """Adds to labor income tracker (called by Handlers)."""
    def add_consumption_expenditure(self, amount: int, item_id: str | None = None) -> None:
        """
        Adds to consumption expenditure tracker (called by Handlers).
        Implements IConsumptionTracker.
        """
    def trigger_emergency_liquidation(self) -> list[Order]:
        """
        WO-167: Trigger panic selling/liquidation for distress.
        Used by LifecycleManager.
        """
    def reset_tick_state(self) -> None:
        '''
        Resets tick-level financial accumulators to zero.
        Adheres to the "Late-Reset Principle".
        '''
    def cast_vote(self, current_tick: int, government_state: Any) -> VoteRecordDTO: ...
