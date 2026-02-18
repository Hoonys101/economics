File: modules\simulation\dtos\api.py
```python
"""
DTOs and Protocols for the Simulation Domain.
Strict adherence to Integer Pennies for all discrete monetary values.
Statistical averages remain floats to preserve precision.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, TYPE_CHECKING, Union, TypedDict
from modules.simulation.dtos.api import FirmStateDTO, HouseholdConfigDTO, FirmConfigDTO
from simulation.models import Order
from simulation.dtos.decision_dtos import DecisionOutputDTO
from modules.finance.api import IFinancialAgent
from modules.simulation.api import AgentID
from modules.governance.api import SystemCommand
from simulation.dtos.commands import GodCommandDTO
from modules.system.api import (
    CurrencyCode,
    MarketSnapshotDTO,
    HousingMarketSnapshotDTO,
    LoanMarketSnapshotDTO,
    LaborMarketSnapshotDTO,
    HousingMarketUnitDTO,
    MarketContextDTO
)
# Phase 1: EconomicIndicatorsDTO from modules.simulation.api
from modules.simulation.api import EconomicIndicatorsDTO

# Alias for standardization
OrderDTO = Order


if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.firms import Firm
    from simulation.dtos.scenario import StressScenarioConfig
    from modules.household.dtos import HouseholdStateDTO

 @dataclass
class TransactionData:
    run_id: int
    time: int
    buyer_id: AgentID
    seller_id: AgentID
    item_id: str
    quantity: float
    price: int  # [REF-PENNY] Converted to Integer Pennies
    currency: CurrencyCode
    market_id: str
    transaction_type: str

 @dataclass
class AgentStateData:
    run_id: int
    time: int
    agent_id: AgentID
    agent_type: str
    assets: Dict[CurrencyCode, int] # [REF-PENNY] Converted to Integer Pennies
    is_active: bool
    is_employed: Optional[bool] = None
    employer_id: Optional[AgentID] = None
    needs_survival: Optional[float] = None
    needs_labor: Optional[float] = None
    inventory_food: Optional[float] = None
    current_production: Optional[float] = None
    num_employees: Optional[int] = None
    education_xp: Optional[float] = None
    generation: Optional[int] = 0
    # Experiment: Time Allocation Tracking
    time_worked: Optional[float] = None
    time_leisure: Optional[float] = None

 @dataclass
class EconomicIndicatorData:
    run_id: int
    time: int
    unemployment_rate: Optional[float] = None
    avg_wage: Optional[float] = None # Averages retain float precision
    food_avg_price: Optional[float] = None # Averages retain float precision
    food_trade_volume: Optional[float] = None
    avg_goods_price: Optional[float] = None # Averages retain float precision
    total_production: Optional[float] = None
    total_consumption: Optional[float] = None
    total_household_assets: Optional[Dict[CurrencyCode, int]] = None # [REF-PENNY] Total is discrete sum -> Int
    total_firm_assets: Optional[Dict[CurrencyCode, int]] = None # [REF-PENNY] Total is discrete sum -> Int
    total_food_consumption: Optional[float] = None
    total_inventory: Optional[float] = None
    avg_survival_need: Optional[float] = None
    total_labor_income: Optional[int] = None # [REF-PENNY] Sum of wages -> Int
    total_capital_income: Optional[int] = None # [REF-PENNY] Sum of dividends/gains -> Int
    # Phase 23: Education & Opportunity Metrics
    avg_education_level: Optional[float] = None
    education_spending: Optional[int] = None # [REF-PENNY] Total spending -> Int
    education_coverage: Optional[float] = None
    brain_waste_count: Optional[int] = None

 @dataclass
class MarketHistoryData:
    time: int
    market_id: str
    item_id: Optional[str] = None
    avg_price: Optional[float] = None # Average
    trade_volume: Optional[float] = None
    best_ask: Optional[int] = None # [REF-PENNY] Discrete Order Price -> Int
    best_bid: Optional[int] = None # [REF-PENNY] Discrete Order Price -> Int
    avg_ask: Optional[float] = None
    avg_bid: Optional[float] = None
    worst_ask: Optional[int] = None # [REF-PENNY] Discrete Order Price -> Int
    worst_bid: Optional[int] = None # [REF-PENNY] Discrete Order Price -> Int

 @dataclass
class AIDecisionData:
    run_id: int
    tick: int
    agent_id: AgentID
    decision_type: str
    decision_details: Optional[Dict[str, Any]] = None
    predicted_reward: Optional[float] = None
    actual_reward: Optional[float] = None

class GoodsDTO(TypedDict, total=False):
    id: str
    name: str
    category: str
    is_durable: bool
    is_essential: bool
    initial_price: int # [REF-PENNY]
    base_need_satisfaction: float
    quality_modifier: float
    # Fields from goods.json
    type: str
    satiety: float
    decay_rate: float

class MarketHistoryDTO(TypedDict, total=False):
    avg_price: float
    trade_volume: float
    best_ask: int # [REF-PENNY]
    best_bid: int # [REF-PENNY]
    avg_ask: float
    avg_bid: float
    worst_ask: int # [REF-PENNY]
    worst_bid: int # [REF-PENNY]

 @dataclass
class GovernmentPolicyDTO:
    """A pure-data snapshot of current government policies affecting agent decisions."""
    income_tax_rate: float
    sales_tax_rate: float
    corporate_tax_rate: float
    base_interest_rate: float

 @dataclass
class DecisionInputDTO:
    """
    Standardized input DTO for agent decision-making.
    Encapsulates all external system inputs passed to make_decision.
    """
    market_snapshot: MarketSnapshotDTO
    goods_data: List[Dict[str, Any]]
    market_data: Dict[str, Any]
    current_time: int
    fiscal_context: Optional[FiscalContext] = None
    macro_context: Optional[MacroFinancialContext] = None
    stress_scenario_config: Optional[Any] = None 
    government_policy: Optional[GovernmentPolicyDTO] = None
    agent_registry: Optional[Dict[str, int]] = None
    housing_system: Optional[Any] = None
    market_context: Optional[MarketContextDTO] = None


 @dataclass
class DecisionContext:
    """
    A pure data container for decision-making.
    Direct agent instance access is strictly forbidden (Enforced by Purity Gate).
    """
    goods_data: List[GoodsDTO]
    market_data: Dict[str, MarketHistoryDTO]
    current_time: int
    
    # State DTO representing the agent's current condition
    state: Union[HouseholdStateDTO, FirmStateDTO]
    
    # Static configuration values relevant to the agent type
    config: Union[HouseholdConfigDTO, FirmConfigDTO]

    # New DTOs
    market_snapshot: Optional[MarketSnapshotDTO] = None
    government_policy: Optional[GovernmentPolicyDTO] = None

    stress_scenario_config: Optional[StressScenarioConfig] = None 

    # Agent Discovery Registry (WO-138)
    agent_registry: Dict[str, AgentID] = field(default_factory=dict)

    # Tick-Snapshot Injection
    market_context: Optional[MarketContextDTO] = None


 @dataclass
class FiscalContext:
    """
    Context providing access to fiscal entities (Government) in a restricted manner.
    """
    government: IFinancialAgent


 @dataclass
class SimulationState:
    """
    WO-103: Simulation State DTO to reduce coupling.
    Passes all necessary data from the Simulation object to system services.
    """
    time: int
    households: List[Household]
    firms: List[Firm]
    agents: Dict[AgentID, Any]
    markets: Dict[str, Any]
    government: Any  # Government
    bank: Any        # Bank
    central_bank: Any # CentralBank
    escrow_agent: Optional[Any] # EscrowAgent
    stock_market: Optional[Any] # StockMarket
    stock_tracker: Optional[Any] # Added for WO-133 Fix
    goods_data: Dict[str, Any]
    market_data: Dict[str, Any] # Added for WO-103
    config_module: Any
    tracker: Any
    logger: Any # logging.Logger
    ai_training_manager: Optional[Any]
    ai_trainer: Optional[Any] # Added for WO-103
    settlement_system: Optional[Any] = None # WO-112: Settlement System
    next_agent_id: int = 0 # Added for WO-103
    real_estate_units: List[Any] = field(default_factory=list) # Added for WO-103
    # Mutable state for the tick
    transactions: List[Any] = None # List[Transaction]
    inter_tick_queue: List[Any] = None # List[Transaction]
    effects_queue: List[Dict[str, Any]] = None # WO-109: Queue for side-effects
    inactive_agents: Dict[AgentID, Any] = None # WO-109: Store inactive agents
    taxation_system: Optional[Any] = None # WO-116: Taxation System
    currency_holders: List[Any] = None # Added for M2 tracking (Phase 33/5)
    stress_scenario_config: Optional[StressScenarioConfig] = None # Phase 28
    transaction_processor: Optional[Any] = None 
    shareholder_registry: Optional[Any] = None 

    # Phase 4.1: Saga Orchestration & Monetary Ledger (TD-253)
    saga_orchestrator: Optional[Any] = None
    monetary_ledger: Optional[Any] = None

    # TD-255: System Command Pipeline
    system_commands: List[SystemCommand] = field(default_factory=list)
    god_commands: List[GodCommandDTO] = field(default_factory=list)

    # --- NEW TRANSIENT FIELDS ---
    firm_pre_states: Dict[AgentID, Any] = None
    household_pre_states: Dict[AgentID, Any] = None
    household_time_allocation: Dict[AgentID, float] = None
    planned_consumption: Optional[Dict[AgentID, Dict[str, Any]]] = None 
    household_leisure_effects: Dict[AgentID, float] = None
    injectable_sensory_dto: Optional[Any] = None 
    currency_registry_handler: Optional[Any] = None 

    def register_currency_holder(self, holder: Any) -> None:
        if self.currency_registry_handler:
            self.currency_registry_handler.register_currency_holder(holder)
        elif self.currency_holders is not None:
             self.currency_holders.append(holder) # Fallback

    def unregister_currency_holder(self, holder: Any) -> None:
        if self.currency_registry_handler:
            self.currency_registry_handler.unregister_currency_holder(holder)
        elif self.currency_holders is not None:
             if holder in self.currency_holders:
                 self.currency_holders.remove(holder) # Fallback

    def __post_init__(self):
        if self.transactions is None: self.transactions = []
        if self.system_commands is None: self.system_commands = []
        if self.god_commands is None: self.god_commands = []
        if self.inter_tick_queue is None: self.inter_tick_queue = []
        if self.effects_queue is None: self.effects_queue = []
        if self.inactive_agents is None: self.inactive_agents = {}
        if self.currency_holders is None: self.currency_holders = []
        if self.firm_pre_states is None: self.firm_pre_states = {}
        if self.household_pre_states is None: self.household_pre_states = {}
        if self.household_time_allocation is None: self.household_time_allocation = {}
        if self.planned_consumption is None: self.planned_consumption = {}
        if self.household_leisure_effects is None: self.household_leisure_effects = {}


# ------------------------------------------------------------------------------
# 주식 시장 및 경제 분석 DTO
# ------------------------------------------------------------------------------

 @dataclass
class StockMarketHistoryData:
    """주식 시장 틱별 이력 (기업별)"""
    run_id: int
    time: int
    firm_id: AgentID
    
    # 주가 관련
    stock_price: int                # [REF-PENNY] 현재 주가 (Discrete) -> Int
    book_value_per_share: float     # 주당 순자산가치 (Calculated Ratio) -> Keep Float
    price_to_book_ratio: float      # PBR
    
    # 거래 관련
    trade_volume: float             
    buy_order_count: int            
    sell_order_count: int           
    
    # 기업 실적 연계
    firm_assets: int                # [REF-PENNY] Total Assets -> Int
    firm_profit: int                # [REF-PENNY] Net Profit -> Int
    dividend_paid: int              # [REF-PENNY] Dividend Payout -> Int
    market_cap: int                 # [REF-PENNY] Market Cap -> Int


 @dataclass
class WealthDistributionData:
    """부의 분배 지표 (틱별)"""
    run_id: int
    time: int
    
    # 자산 분배 (지니계수)
    gini_total_assets: float        
    gini_financial_assets: float    
    gini_stock_holdings: float      
    
    # 소득 분배
    labor_income_share: float       
    capital_income_share: float     
    
    # 분위별 자산 (Statistical Aggregate -> Float implies average/interpolated)
    # However, if these represent strict cutoffs, Int might be better, but standard is Float for percentiles.
    top_10_pct_wealth_share: float  
    bottom_50_pct_wealth_share: float 
    
    # 평균/중위 비교 (Averages)
    mean_household_assets: float
    median_household_assets: float
    mean_to_median_ratio: float     


 @dataclass
class HouseholdIncomeData:
    """가계별 소득 원천 추적"""
    run_id: int
    time: int
    household_id: AgentID
    
    labor_income: int               # [REF-PENNY]
    dividend_income: int            # [REF-PENNY]
    capital_gains: int              # [REF-PENNY]
    total_income: int               # [REF-PENNY]
    
    portfolio_value: int            # [REF-PENNY]
    portfolio_return_rate: float    # Return Rate


 @dataclass
class SocialMobilityData:
    """계층 이동 지표 (틱별)"""
    run_id: int
    time: int
    
    # 계층 구분
    quintile_1_count: int           
    quintile_2_count: int           
    quintile_3_count: int           
    quintile_4_count: int           
    quintile_5_count: int           
    
    # 계층 이동
    upward_mobility_count: int      
    downward_mobility_count: int    
    stable_count: int               
    
    # 분위별 평균 자산 (Average -> Float)
    quintile_1_avg_assets: float
    quintile_2_avg_assets: float
    quintile_3_avg_assets: float
    quintile_4_avg_assets: float
    quintile_5_avg_assets: float
    
    # 계층 고착도
    mobility_index: float           


 @dataclass
class PersonalityStatisticsData:
    """성향별 통계 (틱별)"""
    run_id: int
    time: int
    personality_type: str           
    
    # 기본 통계
    count: int                      
    avg_assets: float               # Average -> Float
    median_assets: float            # Median -> Float
    
    # 소득 구조
    avg_labor_income: float         # Average -> Float
    avg_capital_income: float       # Average -> Float
    labor_income_ratio: float       
    
    # 고용 및 투자
    employment_rate: float          
    avg_portfolio_value: float      # Average -> Float
    avg_stock_holdings: float       
    
    # 욕구 충족
    avg_survival_need: float        
    avg_social_need: float          
    avg_improvement_need: float     
    
    # 성과 지표
    avg_wealth_growth_rate: float   


# ==============================================================================
# Phase 5: Time Allocation & Genealogy DTOs
# ==============================================================================
from typing import Literal

LeisureType = Literal["PARENTING", "SELF_DEV", "ENTERTAINMENT", "IDLE"]

 @dataclass
class TimeBudgetDTO:
    """한 틱(24시간) 동안의 시간 배분 결과"""
    total_hours: float = 24.0
    work_hours: float = 0.0
    leisure_hours: float = 0.0
    selected_leisure_type: LeisureType = "IDLE"
    efficiency_multiplier: float = 1.0 


 @dataclass
class FamilyInfoDTO:
    """가계의 가족 관계 정보 (AI 의사결정용 입력)"""
    agent_id: AgentID
    generation: int
    parent_id: Optional[AgentID]
    children_ids: List[AgentID]
    children_avg_xp: float = 0.0 


 @dataclass
class LeisureEffectDTO:
    """여가 활동의 결과"""
    leisure_type: LeisureType
    leisure_hours: float
    utility_gained: float       
    xp_gained: float           

 @dataclass
class GovernmentSensoryDTO:
    """
    WO-057-B: Sensory Module DTO.
    Transfers 10-tick SMA macro data to the Government Agent.
    """
    tick: int
    inflation_sma: float
    unemployment_sma: float
    gdp_growth_sma: float
    wage_sma: float
    approval_sma: float
    current_gdp: float
    # WO-057-A: Added for AdaptiveGovBrain
    gini_index: float = 0.0
    approval_low_asset: float = 0.5
    approval_high_asset: float = 0.5

 @dataclass
class MacroFinancialContext:
    """
    WO-062: Macro-Linked Portfolio Decisions.
    Transfers macro financial data to portfolio decision modules.
    """
    inflation_rate: float
    gdp_growth_rate: float
    market_volatility: float
    interest_rate_trend: float


 @dataclass
class LaborResult:
    """Represents the result of a household's labor activities for a tick."""
    hours_worked: float
    income_earned: int # [REF-PENNY] Earnings are discrete pennies


 @dataclass
class ConsumptionResult:
    """Represents the result of a household's consumption activities for a tick."""
    items_consumed: Dict[str, float]
    satisfaction: float
```

File: design\3_work_artifacts\specs\spec_dto_reporting_pennies.md
```markdown
# Spec: Reporting DTO Penny Hardening (Integer Migration)

## 1. Introduction
- **Mission**: `spec-dto-reporting-pennies`
- **Objective**: Refactor all monetary fields in Reporting/Analytics DTOs (`simulation/dtos/api.py`) from `float` to `int` (Integer Pennies).
- **Target Debt**: Resolves `TD-DTO-RED-ZONE` (Reporting Leakage) and `TD-TRANS-INT-SCHEMA`.
- **Scope**: `TransactionData`, `AgentStateData`, `EconomicIndicatorData`, `StockMarketHistoryData`, `HouseholdIncomeData`.

## 2. Core Decisions (The Penny Standard)
- **Discrete Values**: All values representing a specific transaction price, a wallet balance, or a total transfer MUST be `int`.
- **Aggregates**: Averages (Mean, Median) and Indices (Gini, Rates) SHALL remain `float` to preserve statistical precision during aggregation.
- **Conversion Rule**: Logic exporting data to these DTOs must use `int(amount * 100)` if coming from legacy float sources, or pass direct `int` if coming from `SettlementSystem`.

## 3. Schema Changes

### 3.1 Transaction & State
| DTO | Field | Old Type | New Type | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `TransactionData` | `price` | `float` | `int` | Discrete exchange value. |
| `AgentStateData` | `assets` | `Dict[str, float]` | `Dict[str, int]` | Wallet balance. |
| `LaborResult` | `income_earned` | `float` | `int` | Paycheck. |

### 3.2 Indicators & History
| DTO | Field | Old Type | New Type | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `EconomicIndicatorData` | `total_labor_income` | `float` | `int` | Sum of integers. |
| `EconomicIndicatorData` | `total_capital_income` | `float` | `int` | Sum of integers. |
| `EconomicIndicatorData` | `total_*_assets` | `Dict[.., float]` | `Dict[.., int]` | Sum of balances. |
| `MarketHistoryData` | `best_ask` / `best_bid` | `float` | `int` | Order Book edge is discrete. |
| `StockMarketHistoryData` | `stock_price` | `float` | `int` | Last trade price. |
| `StockMarketHistoryData` | `market_cap` | `float` | `int` | Shares * Price. |

## 4. Verification & Testing Strategy

### 4.1 Type Checking
- **Static**: Run `mypy modules/simulation/dtos/api.py` to ensure type consistency.
- **Runtime**: Verify `SettlementSystem` outputs can be directly assigned to `TransactionData` without casting to float.

### 4.2 Impact Analysis (Risk)
- **Dashboard Breakage**: The Frontend Dashboard likely expects dollars (float).
    - *Mitigation*: The Serialization Layer (`to_dict` or JSON encoder) responsible for sending data to the UI must implement a `PennyField` serializer that divides by 100, OR the Frontend must be updated to format pennies as currency.
    - *Decision*: This Spec enforces Backend Purity. Formatting is a UI concern.

### 4.3 Migration
- **Legacy Replay**: Old `trace_output` files containing float JSONs will fail to load into new DTOs if strict type validation is applied.
- **Action**: `TraceLoader` utilities must be updated to detect float fields in legacy logs and `int(val * 100)` them during deserialization.

## 5. Mandatory Reporting
- **Insight File**: `communications/insights/spec-dto-reporting-pennies.md` created.
- **Ledger Update**: `TD-DTO-RED-ZONE` marked for resolution upon implementation.
```

File: communications\insights\spec-dto-reporting-pennies.md
```markdown
# Insight: Reporting DTO Penny Hardening

## Context
Refactoring `modules/simulation/dtos/api.py` to enforce the Penny Standard (Integer Math) on reporting and analytics data structures.

## Architectural Decision: Aggregates vs. Discrete
- **Discrete Integrity**: We enforce `int` for all fields representing actual money that exists in a wallet or changed hands (`price`, `balance`, `income`, `market_cap`).
- **Statistical Precision**: We retain `float` for calculated averages (`avg_wage`, `avg_price`, `median_assets`).
    - *Reasoning*: Converting an average like `$10.553` to `1055` pennies loses information useful for trend analysis. Since these are read-only indicators and not used for settlement, floating point dust is acceptable here.

## Technical Debt Identified (New)
1. **Frontend Contract Break**: The Dashboard frontend (`src/`) currently assumes API responses are in Dollars (float). Changing DTOs to Int (Pennies) will cause values to appear 100x larger in the UI until the frontend is updated.
    - *Mitigation*: Added a note to `spec-dto-reporting-pennies.md`.
2. **Legacy Log Incompatibility**: `trace_output.txt` files generated before this change contain floats. Replaying these logs into the new DTOs will require a migration adapter.

## Resolution Status
- **TD-DTO-RED-ZONE**: Addressed. The "Red Zone" (Reporting Layer) is now strictly typed to prevent float leakage back into the simulation core.
- **TD-TRANS-INT-SCHEMA**: `TransactionData.price` is now `int`.

## Verification Evidence
*(Pending Implementation - To be filled by Implementer)*
- `pytest tests/test_dto_integrity.py` should pass.
```