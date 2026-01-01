import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# --- Simulation Parameters ---
from enum import Enum

# --- Simulation Parameters ---
NUM_HOUSEHOLDS = 20
NUM_FIRMS = 4
SIMULATION_TICKS = 100
HOUSEHOLD_MIN_FOOD_INVENTORY = 2.0 # Rule-based households aim to keep at least this much food in inventory

class EngineType(Enum):
    RULE_BASED = "RuleBased"
    AI_DRIVEN = "AIDriven"

DEFAULT_ENGINE_TYPE = EngineType.AI_DRIVEN  # Can be RULE_BASED or AI_DRIVEN

# --- Initial Agent Configuration ---
INITIAL_HOUSEHOLD_ASSETS_MEAN = 5000.0
INITIAL_HOUSEHOLD_ASSETS_RANGE = 0.2
INITIAL_HOUSEHOLD_LIQUIDITY_NEED_MEAN = 50.0
INITIAL_HOUSEHOLD_LIQUIDITY_NEED_RANGE = 0.2
INITIAL_HOUSEHOLD_NEEDS_MEAN = {
    "survival": 60.0,
    "asset": 10.0,
    "social": 20.0,
    "improvement": 10.0,
    "survival_need": 60.0,
    "recognition_need": 20.0,
    "growth_need": 10.0,
    "wealth_need": 10.0,
    "imitation_need": 15.0,
    "labor_need": 0.0,
    "child_rearing_need": 0.0,
}
INITIAL_HOUSEHOLD_NEEDS_RANGE = 0.1
INITIAL_EMPLOYMENT_RATE = 0.5  # 초기 고용률

INITIAL_FIRM_CAPITAL_MEAN = 10000.0
INITIAL_FIRM_CAPITAL_RANGE = 0.2
INITIAL_FIRM_LIQUIDITY_NEED_MEAN = 200.0
INITIAL_FIRM_LIQUIDITY_NEED_RANGE = 0.2
INITIAL_FIRM_INVENTORY_MEAN = 100.0
INITIAL_FIRM_INVENTORY_RANGE = 0.2
FIRM_PRODUCTIVITY_FACTOR = 10.0

# --- Goods Configuration ---
GOODS = {
    "basic_food": {"production_cost": 3, "initial_price": 5.0, "utility_effects": {"survival": 10}},
    "clothing": {"production_cost": 5, "initial_price": 15.0, "utility_effects": {"survival": 2, "social": 8}},
    "luxury_food": {
        "production_cost": 10,
        "initial_price": 30.0,
        "utility_effects": {"survival": 12, "social": 5},
    },
    "education_service": {
        "production_cost": 20,
        "initial_price": 50.0,
        "utility_effects": {"improvement": 15},
        "is_service": True,
    },
}


# Added for explicit reference
GOODS_INITIAL_PRICE = {
    "basic_food": 5.0,
    "stock": 50.0
}


# --- Firm Specialization ---
# Assigns which firms produce which goods. Assumes NUM_FIRMS = 5 (for multi-good test)
FIRM_SPECIALIZATIONS = {
    0: "basic_food",
    1: "basic_food",
    2: "basic_food",
    3: "clothing",
    4: "clothing",
}


# --- Experiment Configuration ---
FOOD_SUPPLY_MODIFIER = 1.5  # Multiplier for food supply in experiments (e.g., 1.0 for no change, 1.5 for 50% increase, 0.5 for 50% decrease)
INITIAL_HOUSEHOLD_FOOD_INVENTORY = 10.0

# --- Value Orientations (as strings) ---
VALUE_ORIENTATION_WEALTH_AND_NEEDS = "wealth_and_needs"
VALUE_ORIENTATION_NEEDS_AND_GROWTH = "needs_and_growth"
VALUE_ORIENTATION_NEEDS_AND_SOCIAL_STATUS = "needs_and_social_status"

# --- Market & Decision Logic ---
INITIAL_WAGE = 10.0  # Renamed from LABOR_MARKET_OFFERED_WAGE
BASE_WAGE = 20.0
WAGE_INFLATION_ADJUSTMENT_FACTOR = 0.1
LABOR_MARKET_MIN_WAGE = 8.0
HOUSEHOLD_MIN_WAGE_DEMAND = 10.0
HOUSEHOLD_RESERVATION_PRICE_BASE = 5.0
HOUSEHOLD_NEED_PRICE_MULTIPLIER = 1.0
HOUSEHOLD_ASSET_PRICE_MULTIPLIER = 0.1
HOUSEHOLD_PRICE_ELASTICITY_FACTOR = 0.5
HOUSEHOLD_STOCKPILING_BONUS_FACTOR = 0.2
MIN_SELL_PRICE = 1.0
MAX_SELL_PRICE = 100.0
MAX_SELL_QUANTITY = 50.0
PERCEIVED_PRICE_UPDATE_FACTOR = 0.1
INVENTORY_HOLDING_COST_RATE = 0.005
DIVIDEND_RATE = 0.1  # 기본 배당률
DIVIDEND_RATE_MIN = 0.05  # 최소 배당률 (저배당 정책)
DIVIDEND_RATE_MAX = 0.5   # 최대 배당률 (고배당 정책)
WAGE_DECAY_RATE = 0.9
RND_WAGE_PREMIUM = 1.5
WAGE_COMPETITION_PREMIUM = 0.2

# --- Dynamic Wage Determination ---
PROFIT_HISTORY_TICKS = 10  # Number of recent ticks to evaluate a firm's profitability
WAGE_PROFIT_SENSITIVITY = 0.5  # Sensitivity of wage premium to firm's profit
MAX_WAGE_PREMIUM = (
    1.0  # Maximum wage premium based on profitability (100% of base wage)
)

# --- Production & Stock ---
OVERSTOCK_THRESHOLD = 1.2
UNDERSTOCK_THRESHOLD = 0.8
FIRM_MIN_EMPLOYEES = 1
FIRM_MAX_EMPLOYEES = 50
FIRM_MIN_PRODUCTION_TARGET = 10.0
FIRM_MAX_PRODUCTION_TARGET = 500.0
PRODUCTION_ADJUSTMENT_FACTOR = 0.2
PRICE_ADJUSTMENT_FACTOR = 0.2
PRICE_ADJUSTMENT_EXPONENT = 1.2

# --- AI Price Adjustment ---
AI_PRICE_ADJUSTMENT_SMALL = 0.05  # 5% price adjustment
AI_PRICE_ADJUSTMENT_MEDIUM = 0.10  # 10% price adjustment

# --- Need Dynamics & Thresholds ---
BASE_DESIRE_GROWTH = 1.0  # Base rate at which desires increase per tick
MAX_DESIRE_VALUE = 100.0  # Maximum value a desire can reach

# Old need increase rates (commented out as they are replaced by personality-driven growth)
# SURVIVAL_NEED_INCREASE_RATE = 1.0
# RECOGNITION_NEED_INCREASE_RATE = 0.5
# GROWTH_NEED_INCREASE_RATE = 0.3
LIQUIDITY_NEED_INCREASE_RATE = 0.2
# WEALTH_NEED_INCREASE_RATE = 0.1
# IMITATION_NEED_INCREASE_RATE = 0.4
# CHILD_REARING_NEED_INCREASE_RATE = 0.1

SURVIVAL_NEED_THRESHOLD = 20.0
LABOR_NEED_THRESHOLD = 50.0
GROWTH_NEED_THRESHOLD = 60.0
IMITATION_NEED_THRESHOLD = 70.0
CHILD_REARING_NEED_THRESHOLD = 80.0
RECOGNITION_NEED_THRESHOLD = 40.0
WEALTH_NEED_THRESHOLD = 70.0
NEED_MEDIUM_THRESHOLD = 50.0
NEED_HIGH_THRESHOLD = 80.0
SURVIVAL_TO_LABOR_NEED_FACTOR = 0.5

# --- Household Consumption ---
TARGET_FOOD_BUFFER_QUANTITY = 5.0 # 가계가 목표로 하는 식량 완충 재고량.
PERCEIVED_FAIR_PRICE_THRESHOLD_FACTOR = 0.9 # 인지된 공정 가격 대비 얼마나 낮아야 투기적 구매를 고려할지 결정하는 요소.
SURVIVAL_NEED_CONSUMPTION_THRESHOLD = (
    50.0  # Households will try to consume food if survival need is above this
)
FOOD_CONSUMPTION_QUANTITY = 1.0  # Quantity of food consumed at a time
FOOD_CONSUMPTION_MAX_PER_TICK = (
    5.0  # Maximum quantity of food a household can consume in a single tick
)
FOOD_PURCHASE_MAX_PER_TICK = (
    5.0  # Maximum quantity of food a household can purchase in a single tick
)
HOUSEHOLD_MAX_PURCHASE_QUANTITY = 5.0 # Max units per item per tick for bulk buying
HOUSEHOLD_FOOD_PRICE_ELASTICITY = (
    0.5  # Factor to adjust demand based on price deviation from average
)
HOUSEHOLD_FOOD_STOCKPILE_TARGET_TICKS = (
    5  # How many ticks worth of food a household aims to stockpile when prices are good
)
HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0  # The base amount of food a household consumes per tick, to calculate stockpile target
HOUSEHOLD_MIN_FOOD_INVENTORY_TICKS = (
    2  # Minimum number of ticks worth of food a household aims to keep in inventory
)

# --- Agent Lifecycle & Death ---
SURVIVAL_NEED_DEATH_THRESHOLD = 100.0
ASSETS_DEATH_THRESHOLD = 0.0
HOUSEHOLD_DEATH_TURNS_THRESHOLD = 4
ASSETS_CLOSURE_THRESHOLD = 0.0
FIRM_CLOSURE_TURNS_THRESHOLD = 4

# --- Social & Lifecycle & AI ---
SOCIAL_STATUS_ASSET_WEIGHT = 0.3
SOCIAL_STATUS_LUXURY_WEIGHT = 0.7
INITIAL_CHILD_ASSETS_FACTOR = 0.5
RND_PRODUCTIVITY_MULTIPLIER = 0.01
AI_SKILL_REWARD_WEIGHT = 10.0
AI_ASSET_REWARD_WEIGHT = 1.0
AI_SOCIAL_STATUS_REWARD_WEIGHT = 5.0
AI_GROWTH_REWARD_WEIGHT = 7.0
AI_WEALTH_REWARD_WEIGHT = 3.0

# --- AI Learning Parameters ---
AI_GAMMA = 0.9
AI_EPSILON = 0.1
AI_BASE_ALPHA = 0.1
AI_LEARNING_FOCUS = 0.5
THRESHOLD_FORCED_LABOR_EXPLORATION = 1.0
FORCED_LABOR_WAGE_FACTOR = 0.8
HOUSEHOLD_ASSETS_THRESHOLD_FOR_LABOR_SUPPLY = 1.0
FORCED_LABOR_EXPLORATION_PROBABILITY = 0.5
IMITATION_ASSET_THRESHOLD = 500.0
CHILD_REARING_ASSET_THRESHOLD = 1000.0
SURVIVAL_NEED_THRESHOLD_FOR_OTHER_ACTIONS = 30.0
ASSETS_THRESHOLD_FOR_OTHER_ACTIONS = 200.0
IMITATION_LEARNING_INTERVAL = 100
IMITATION_MUTATION_RATE = 0.1
IMITATION_MUTATION_MAGNITUDE = 0.05

# --- Maslow Hierarchy ---
MASLOW_SURVIVAL_THRESHOLD = 50.0  # 이 값 초과 시 상위 욕구 비활성화

# --- Education Service ---
EDUCATION_SENSITIVITY = 0.1       # 교육 효과 민감도
BASE_LEARNING_RATE = 0.1          # 기본 학습률
MAX_LEARNING_RATE = 0.5           # 최대 학습률
LEARNING_EFFICIENCY = 1.0         # XP 획득 효율


# --- Loan Market (Deprecated/Legacy - overwritten by Banking below) ---
LOAN_INTEREST_RATE = 0.05
INITIAL_BANK_ASSETS = 1000000.0
HOUSEHOLD_LOAN_THRESHOLD = 500.0
LOAN_DURATION = 20
DEFAULT_LOAN_DURATION = 10

# --- Banking & Time Scale (Phase 3) ---
TICKS_PER_YEAR = 100.0          # 1년 = 100틱 (모든 이자 계산의 기준)
INITIAL_BASE_ANNUAL_RATE = 0.05 # 연 5% (틱당 금리가 아님!)
LOAN_DEFAULT_TERM = 50          # 6개월 (50틱)
CREDIT_SPREAD_BASE = 0.02       # 연 2% 가산금리
BANK_MARGIN = 0.02              # 예대마진 (연 2%)


# --- Liquidity ---
LIQUIDITY_RATIO_MAX = 0.8
LIQUIDITY_RATIO_MIN = 0.1
LIQUIDITY_RATIO_DIVISOR = 100.0

# --- Database Batching ---
BATCH_SAVE_INTERVAL = 1  # Save to DB every tick (Required for client-driven mode)

# --- Logging ---
ROOT_LOGGER_LEVEL = "INFO"

# --- Security ---
SECRET_TOKEN = os.getenv("SECRET_TOKEN", "default-secret-token")

# ==============================================================================
# Phase 4: Fiscal Policy & Welfare Constants
# ==============================================================================
# 1. Progressive Tax (Income Tax)
# Format: (Threshold Multiplier of SURVIVAL_COST, Tax Rate)
# Example: (1.5, 0.0) -> Income up to 1.5x Survival Cost is Tax Free.
# [HOTFIX: Fiscal Balance] Tax rates reduced by 50% to prevent liquidity crunch
TAX_BRACKETS = [
    (0.5, 0.0),   # Up to 0.5x survival cost: Tax Free
    (1.0, 0.05),  # Working Class (0.5 ~ 1.0x): 5% (was 10%)
    (3.0, 0.10),  # Middle Class: 10% (was 20%)
    (float('inf'), 0.20) # Wealthy: 20% (was 40%)
]

# 2. Wealth Tax (Annual Rate -> Tick Rate Logic needed in implementation)
ANNUAL_WEALTH_TAX_RATE = 0.02  # 2% per year
WEALTH_TAX_THRESHOLD = 50000.0 # Net Worth above this is taxed

# 3. Welfare
# [HOTFIX: Fiscal Balance] Increased to prevent early extinction
UNEMPLOYMENT_BENEFIT_RATIO = 0.7  # 70% of Survival Cost (was 50%)
STIMULUS_TRIGGER_GDP_DROP = -0.05 # -5% GDP Growth triggers Stimulus

# 4. Bankruptcy & Credit Jail
CREDIT_RECOVERY_TICKS = 100       # 1 Year Loan Ban
BANKRUPTCY_XP_PENALTY = 0.2       # 20% XP Loss

# 5. Experiment: Laffer Curve
TAX_MODE = "PROGRESSIVE"  # "PROGRESSIVE" or "FLAT"
BASE_INCOME_TAX_RATE = 0.2  # Used when TAX_MODE="FLAT"
RANDOM_SEED = 42  # For experiment reproducibility

# ==============================================================================
# Phase 5: Time Allocation & Leisure Constants
# ==============================================================================
HOURS_PER_TICK = 24.0
SHOPPING_HOURS = 2.0   # 쇼핑 및 가사 시간 (고정)
MAX_WORK_HOURS = 14.0  # 법정/물리적 최대 노동 시간
LEISURE_WEIGHT = 0.3   # AI 보상 함수에서 여가 효용의 가중치

# 여가 유형별 계수
LEISURE_COEFFS = {
    "PARENTING": {
        "condition_item": "education_service",
        "utility_per_hour": 2.0,   # 시간당 사회적 만족
        "xp_gain_per_hour": 0.5    # 시간당 자녀 XP 증가
    },
    "ENTERTAINMENT": {
        "condition_item": "luxury_food",  # or clothing
        "utility_per_hour": 5.0,   # 높은 즉각적 만족
        "xp_gain_per_hour": 0.0
    },
    "SELF_DEV": {
        "condition_item": None,    # Default (조건 없음)
        "utility_per_hour": 1.0,   # 낮은 만족
        "productivity_gain": 0.001 # 본인 생산성 향상
    }
}


# ==============================================================================
# 🔧 HARDCODED VALUES CENTRALIZATION
# ==============================================================================
# 아래 값들은 코드 전반에 하드코딩되어 있던 것들을 통합 관리하기 위해 이동함.
# 각 섹션은 역할에 따라 분류되어 있으며, 향후 AI가 동적으로 조정해야 할 값들은
# 별도 섹션으로 분리되어 있음.
# ==============================================================================

# ------------------------------------------------------------------------------
# 📊 HOUSEHOLD DECISION LOGIC (가계 의사결정 로직)
# ------------------------------------------------------------------------------
# 가계의 희망 임금 결정에 사용되는 값들
HOUSEHOLD_LOW_ASSET_THRESHOLD = 100.0  # 자산이 이 값 미만이면 낮은 임금 수용
HOUSEHOLD_LOW_ASSET_WAGE = 8.0         # 자산이 낮을 때 희망 임금
HOUSEHOLD_DEFAULT_WAGE = 10.0          # 기본 희망 임금

# 시장 가격 폴백 (시장 데이터 없을 때 사용)
MARKET_PRICE_FALLBACK = 10.0

# ------------------------------------------------------------------------------
# 🏢 FIRM DECISION LOGIC (기업 의사결정 로직)
# ------------------------------------------------------------------------------
# 기업 주식 관련
FIRM_DEFAULT_TOTAL_SHARES = 100.0  # 기업의 기본 총 주식 수

# 고용 임계값
FIRM_LABOR_REQUIREMENT_RATIO = 0.9  # 필요 노동력 대비 현재 고용 비율 임계값

# ------------------------------------------------------------------------------
# 🤖 AI-ADJUSTABLE PARAMETERS (AI 동적 조정 대상)
# ------------------------------------------------------------------------------
# ⚠️ 주의: 아래 값들은 향후 AI 학습 또는 메타 최적화를 통해
# 자동으로 조정될 수 있도록 설계되어야 함.
# 변경 시 시뮬레이션 전체 동작에 영향을 미칠 수 있음.
# ------------------------------------------------------------------------------

# --- 욕구 기반 가치 평가 (Need-Based Valuation) ---
NEED_FACTOR_BASE = 0.5              # 욕구 팩터 기본값 (max_need=0일 때)
NEED_FACTOR_SCALE = 100.0           # 욕구값을 정규화하는 스케일
VALUATION_MODIFIER_BASE = 0.9       # 가치 평가 수정자 기본값
VALUATION_MODIFIER_RANGE = 0.2      # 가치 평가 수정자 범위 (agg_buy에 따라 변동)

# --- 욕구 임계값 (Need Thresholds for Bulk Buying) ---
BULK_BUY_NEED_THRESHOLD = 70.0      # 이 값 이상이면 대량 구매
BULK_BUY_AGG_THRESHOLD = 0.8        # 공격성이 이 값 이상이면 추가 구매
BULK_BUY_MODERATE_RATIO = 0.6       # 보통 패닉 구매 시 최대 수량 비율

# --- 예산 제한 (Budget Constraints) ---
BUDGET_LIMIT_NORMAL_RATIO = 0.5     # 일반 상황에서 자산 대비 예산 비율
BUDGET_LIMIT_URGENT_NEED = 80.0     # 이 욕구 이상이면 긴급 예산 적용
BUDGET_LIMIT_URGENT_RATIO = 0.9     # 긴급 상황에서 자산 대비 예산 비율

# --- 직장 이동 (Job Mobility) ---
JOB_QUIT_THRESHOLD_BASE = 2.0       # 기본 퇴직 임계값 (낮은 이동성일 때)
JOB_QUIT_PROB_BASE = 0.1            # 퇴직 확률 기본값
JOB_QUIT_PROB_SCALE = 0.9           # 퇴직 확률 스케일 (agg_mobility에 따라 변동)

# --- 유보 임금 (Reservation Wage) ---
RESERVATION_WAGE_BASE = 1.5         # 유보 임금 계산 기본값
RESERVATION_WAGE_RANGE = 1.0        # 유보 임금 계산 범위

# --- 최소 구매 수량 (Minimum Purchase Quantity) ---
MIN_PURCHASE_QUANTITY = 0.1         # 구매를 실행하기 위한 최소 수량

# ------------------------------------------------------------------------------
# 🎓 AI HYPERPARAMETERS (AI 학습 하이퍼파라미터)
# ------------------------------------------------------------------------------
# 이 값들은 Q-러닝 기반 AI 학습에 사용됨.
# 현재 default argument로 사용되며, config에서 우선 참조 가능.
# AI_GAMMA, AI_EPSILON, AI_BASE_ALPHA, AI_LEARNING_FOCUS 는 이미 위에 정의됨.

# 상위/하위 에이전트 선별 백분위
TOP_PERFORMING_PERCENTILE = 0.1     # 상위 10% 에이전트 (모방 학습 대상)
UNDER_PERFORMING_PERCENTILE = 0.5   # 하위 50% 에이전트 (학습 필요 대상)

# --- 가격 결정 AI (AI Price Decision) ---
AI_MIN_PRICE_FLOOR = 0.1            # AI가 설정 가능한 최저 가격 하한

# ------------------------------------------------------------------------------
# 📈 STOCK MARKET PARAMETERS (주식 시장 파라미터)
# ------------------------------------------------------------------------------
# 주식 시장 운영에 필요한 설정값들

# --- 기본 설정 ---
STOCK_MARKET_ENABLED = True         # 주식 시장 활성화 여부
STOCK_PRICE_LIMIT_RATE = 0.10       # 일일 가격 변동폭 제한 (±10%)

# --- 주가 결정 방식 ---
STOCK_PRICE_METHOD = "book_value"   # "book_value" 또는 "market_price"
STOCK_BOOK_VALUE_MULTIPLIER = 1.0   # 순자산가치 대비 기준 주가 배수 (PBR)

# --- 거래 관련 ---
STOCK_MIN_ORDER_QUANTITY = 1.0      # 최소 주문 수량
STOCK_ORDER_EXPIRY_TICKS = 5        # 주문 유효 기간 (틱)
STOCK_TRANSACTION_FEE_RATE = 0.001  # 거래 수수료율 (0.1%)

# --- 투자 의사결정 ---
HOUSEHOLD_INVESTMENT_BUDGET_RATIO = 0.2  # 자산 대비 최대 투자 비율
HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT = 500.0  # 투자를 위한 최소 자산
STOCK_SELL_PROFIT_THRESHOLD = 0.15  # 매도 고려 수익률 임계값 (15%)
STOCK_BUY_DISCOUNT_THRESHOLD = 0.10 # 매수 고려 할인율 임계값 (10%)

# --- Phase 3.1: Government & Taxation ---
INCOME_TAX_RATE = 0.1                 # 가계 소득세 (10%)
INCOME_TAX_PAYER = "HOUSEHOLD"         # "HOUSEHOLD" (원천징수) 또는 "FIRM" (기업이 추가 납부)
CORPORATE_TAX_RATE = 0.2              # 기업 법인세 (20%)
SALES_TAX_RATE = 0.05                 # 거래세/부가세 (5%)
INHERITANCE_TAX_RATE = 1.0            # 상속세 (100%, 정부 귀속)

RD_SUBSIDY_RATE = 0.2                 # R&D(자본투자) 보조금 (투자액의 20%)
INFRASTRUCTURE_INVESTMENT_COST = 5000.0  # 인프라 투자 1회당 비용
INFRASTRUCTURE_TFP_BOOST = 0.05       # 인프라 투자 시 전체 생산성(TFP) 증가율

# --- 배당 관련 (기존 DIVIDEND_RATE 참조) ---
# DIVIDEND_RATE는 이미 위에서 정의됨

# --- 창업 관련 ---
STARTUP_MIN_CAPITAL = 5000.0        # 창업 최소 자본금
STARTUP_INITIAL_SHARES = 100.0      # 창업 시 발행 주식 수
STARTUP_PROBABILITY = 0.01          # 틱당 창업 시도 확률 (자격 충족 시)

# --- Mitosis Configuration ---
TARGET_POPULATION = 50
MITOSIS_BASE_THRESHOLD = 5000.0  # 기본 분열 자산 요건
MITOSIS_SENSITIVITY = 1.5       # 인구 압박 민감도
MITOSIS_SURVIVAL_THRESHOLD = 20.0  # 배고픔 한계
MITOSIS_MUTATION_PROBABILITY = 0.2  # 성격 돌연변이 확률
MITOSIS_Q_TABLE_MUTATION_RATE = 0.05  # Q-table 노이즈 비율

# --- Phase 4: Fiscal Policy ---

# 1. Progressive Tax (Income Tax)
# Criteria: Multiples of SURVIVAL_COST
# [HOTFIX: Fiscal Balance] Tax rates reduced by 50%
TAX_BRACKETS = [
    (0.5, 0.0),   # Tax Free
    (1.0, 0.05),  # Working Class: 5% (was 10%)
    (3.0, 0.10),  # Middle Class: 10% (was 20%)
    (float('inf'), 0.20) # Wealthy: 20% (was 40%)
]

# 2. Wealth Tax
# WEALTH_TAX_THRESHOLD is defined below
WEALTH_TAX_THRESHOLD = 50000.0
ANNUAL_WEALTH_TAX_RATE = 0.02   # Annual 2% wealth tax

# 3. Welfare
# [HOTFIX: Fiscal Balance] Increased to 0.7
UNEMPLOYMENT_BENEFIT_RATIO = 0.7 # 70% of survival cost (was 50%)
STIMULUS_TRIGGER_GDP_DROP = -0.05 # GDP 5% drop trigger

# 4. Bankruptcy Penalty
CREDIT_RECOVERY_TICKS = 100 # 1 year (100 ticks) credit jail
BANKRUPTCY_XP_PENALTY = 0.2 # 20% XP penalty

FISCAL_MODEL = "MIXED" # Default regime
    
# ==============================================================================
# Phase 6: The Brand Economy
# ==============================================================================
# 1. Brand Engine
MARKETING_DECAY_RATE = 0.8        # Adstock retains 80% per tick
MARKETING_EFFICIENCY = 0.01       # 1 unit of currency = 0.01 adstock unit
PERCEIVED_QUALITY_ALPHA = 0.2     # EMA smoothing factor for quality perception

# 2. Consumer Behavior
QUALITY_SENSITIVITY_MEAN = 0.5    # Average preference for quality over price
BRAND_LOYALTY_DECAY = 0.95        # Loyalty score decays 5% per tick without reinforcement
NETWORK_EFFECT_WEIGHT = 0.5       # Weight of sales volume in Utility function

# 3. AI Reward
# AI_VALUATION_MULTIPLIER = 1000.0   # Deprecated: Using relative asset valuation (5% of Assets * Delta Awareness)

# ==============================================================================
# Task #9: Entrepreneurship Constants
# ==============================================================================
MIN_FIRMS_THRESHOLD = 5          # 최소 기업 수 (이하로 떨어지면 창업 유도)
STARTUP_COST = 15000.0           # 창업 비용 (가계 현금에서 차감)
ENTREPRENEURSHIP_SPIRIT = 0.05   # 자격 있는 가계의 창업 확률 (5%)
STARTUP_CAPITAL_MULTIPLIER = 1.5 # 창업 자격: cash > STARTUP_COST * 이 값
