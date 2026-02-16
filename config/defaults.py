from enum import Enum
import os

# --- Phase 21: Corporate Empires ---
AUTOMATION_LABOR_REDUCTION = 0.1  # Max 50% reduction in labor alpha
AUTOMATION_COST_PER_PCT = 1000000  # Base cost to increase automation by 1% (scaled by assets) - MIGRATION: Int pennies
HOSTILE_TAKEOVER_DISCOUNT_THRESHOLD = 0.7  # Target if Market Cap < 70% of Intrinsic Value

# --- Phase 21.5: Stabilization (WO-044) ---
# LABOR_ELASTICITY_MIN moved to Phase 21.6
SEVERANCE_PAY_WEEKS = 4             # 해고 시 4주치 임금 지급

# --- Phase 21.6: The Invisible Hand (WO-045) ---
LABOR_ELASTICITY_MIN = 0.0              # 가드레일 제거
RESERVATION_WAGE_FLOOR_RATIO = 0.7      # 시장 평균의 70% 미만 거부
WAGE_DECAY_RATE = 0.02                  # 실업 시 희망임금 하락률 (2%/틱)
WAGE_RECOVERY_RATE = 0.01               # 취업 시 희망임금 상승률 (1%/틱)
RESERVATION_WAGE_FLOOR = 0.3            # 최저 희망임금 (시장 평균의 30%)
SURVIVAL_CRITICAL_TURNS = 5             # 생존 가능 잔여 기간 임계값


# --- Phase 20: The Matrix v1 ---
SYSTEM2_TICKS_PER_CALC = 10
SYSTEM2_HORIZON = 100
SYSTEM2_DISCOUNT_RATE = 0.98
FORMULA_TECH_LEVEL = 0.0
LACTATION_INTENSITY = 1.0
HOMEWORK_QUALITY_COEFF = 0.5

# --- Phase 20-3: Immigration ---
POPULATION_IMMIGRATION_THRESHOLD = 80
IMMIGRATION_BATCH_SIZE = 5

# --- Phase 17-4: Vanity System ---
ENABLE_VANITY_SYSTEM = True
VANITY_WEIGHT = 1.5           # 허영심 강도 (0=불교, 1=자본주의, 1.5=헬조선)
MIMICRY_FACTOR = 0.5          # 모방 소비 강도
REFERENCE_GROUP_PERCENTILE = 0.20  # 상위 20%

# 성격 유형별 Conformity 범위 (Biased Randomization)
CONFORMITY_RANGES = {
    "STATUS_SEEKER": (0.7, 0.95),
    "CONSERVATIVE": (0.5, 0.7),
    "MISER": (0.1, 0.3),
    "IMPULSIVE": (0.4, 0.6),  # 중간
    # 기본값
    None: (0.3, 0.7)
}

# --- Gold Standard Mode (WO-016) ---
GOLD_STANDARD_MODE = False  # True: 금본위 (Full Reserve), False: 현대 금융 (Credit Creation)
RESERVE_REQ_RATIO = 0.1    # 지급준비율 (10%) - WO-064
INITIAL_MONEY_SUPPLY = 10000000  # 초기 화폐 총량 (검증용 기준값) - MIGRATION: Int pennies

# --- Simulation Parameters ---
NUM_HOUSEHOLDS = 20
NUM_FIRMS = 4
SIMULATION_TICKS = 1000
HOUSEHOLD_MIN_FOOD_INVENTORY = 0.0 # Operation Empty Warehouse: No initial safety net
TARGET_FOOD_BUFFER_QUANTITY = 5.0 # WO-023: Maslow Constraint Threshold

class EngineType(Enum):
    RULE_BASED = "RuleBased"
    AI_DRIVEN = "AIDriven"

DEFAULT_ENGINE_TYPE = EngineType.AI_DRIVEN  # Can be RULE_BASED or AI_DRIVEN
NEWBORN_ENGINE_TYPE = "AIDriven"  # Default engine for newborns: "AIDriven" or "RuleBased"

# --- Initial Agent Configuration ---
INITIAL_HOUSEHOLD_ASSETS_RANGE = 0.2
INITIAL_HOUSEHOLD_LIQUIDITY_NEED_MEAN = 5000 # MIGRATION: Int pennies
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
    "labor_need": 0.0,
    "child_rearing_need": 0.0,
    "quality": 0.0, # WO-023: New need for consumer goods
}
INITIAL_HOUSEHOLD_NEEDS_RANGE = 0.1
INITIAL_EMPLOYMENT_RATE = 0.5  # 초기 고용률

INITIAL_FIRM_CAPITAL_MEAN = 1000000 # High Initial Capital for Laissez-Faire Runway - MIGRATION: Int pennies
INITIAL_FIRM_CAPITAL_RANGE = 0.2
INITIAL_FIRM_LIQUIDITY_NEED_MEAN = 20000 # MIGRATION: Int pennies
INITIAL_FIRM_LIQUIDITY_NEED_RANGE = 0.2
INITIAL_FIRM_INVENTORY_MEAN = 0.0  # Operation Empty Warehouse: No initial safety net
INITIAL_FIRM_INVENTORY_RANGE = 0.2
FIRM_PRODUCTIVITY_FACTOR = 20.0 # Laissez-Faire: Double Output

# --- Goods Configuration ---
GOODS = {
    "basic_food": {
        "production_cost": 300, # MIGRATION: Int pennies
        "initial_price": 500, # MIGRATION: Int pennies
        "utility_effects": {"survival": 10},
        "is_luxury": False,
        "sector": "FOOD",
    },
    "clothing": {
        "production_cost": 500, # MIGRATION: Int pennies
        "initial_price": 1500, # MIGRATION: Int pennies
        "utility_effects": {"survival": 2, "social": 8},
        "is_luxury": True,
        "sector": "GOODS",
    },
    "luxury_food": {
        "production_cost": 1000, # MIGRATION: Int pennies
        "initial_price": 3000, # MIGRATION: Int pennies
        "utility_effects": {"survival": 12, "social": 5},
        "is_luxury": True,
        "sector": "FOOD",
    },
    "education_service": {
        "production_cost": 2000, # MIGRATION: Int pennies
        "initial_price": 5000, # MIGRATION: Int pennies
        "utility_effects": {"improvement": 15},
        "is_service": True,
        "is_luxury": False,
        "sector": "SERVICE",
    },
    # WO-030: Iron (Raw Material)
    "iron": {
        "production_cost": 200, # MIGRATION: Int pennies
        "initial_price": 800, # MIGRATION: Int pennies
        "utility_effects": {},
        "is_luxury": False,
        "sector": "MATERIAL",
    },
    # WO-023: Consumer Goods (Industrial Product)
    "consumer_goods": {
        "production_cost": 500, # MIGRATION: Int pennies
        "initial_price": 1500, # MIGRATION: Int pennies
        "utility_effects": {"quality": 10},
        "is_luxury": True, # Treated as luxury/higher tier need
        "sector": "GOODS",
        "is_durable": True,
        "base_lifespan": 50,  # Ticks
        "quality_sensitivity": 0.5,
        "inputs": {"iron": 1.0}, # WO-030: 1 unit of iron per unit of consumer_goods
    },
    "luxury_bag": {
        "production_cost": 50000, # MIGRATION: Int pennies
        "initial_price": 200000, # MIGRATION: Int pennies
        "utility_effects": {"social": 50},
        "is_luxury": True,
        "is_veblen": True,  # 가격↑ → 수요↑
        "sector": "LUXURY",
    },
}

RAW_MATERIAL_SECTORS = ["iron"]

HOUSEHOLD_CONSUMABLE_GOODS = ["basic_food", "luxury_food"]


# Added for explicit reference
GOODS_INITIAL_PRICE = {
    "basic_food": 500, # MIGRATION: Int pennies
    "stock": 5000 # MIGRATION: Int pennies
}


# --- Firm Specialization ---
DEFAULT_UNIT_COST = 500  # Default unit cost for firms (pennies)
SPACE_UTILITY_FACTOR = 1.0 # Utility factor for space

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

# --- 3-Pillars Preference Mapping ---
VALUE_ORIENTATION_MAPPING = {
    VALUE_ORIENTATION_WEALTH_AND_NEEDS: {
        "preference_asset": 1.3,
        "preference_social": 0.7,
        "preference_growth": 1.0,
    },
    VALUE_ORIENTATION_NEEDS_AND_GROWTH: {
        "preference_asset": 0.8,
        "preference_social": 0.7,
        "preference_growth": 1.5,
    },
    VALUE_ORIENTATION_NEEDS_AND_SOCIAL_STATUS: {
        "preference_asset": 0.7,
        "preference_social": 1.5,
        "preference_growth": 0.8,
    },
}

# --- Market & Decision Logic ---
INITIAL_WAGE = 1000  # Renamed from LABOR_MARKET_OFFERED_WAGE
BASE_WAGE = 2000
WAGE_INFLATION_ADJUSTMENT_FACTOR = 0.1
LABOR_MARKET_MIN_WAGE = 800
HOUSEHOLD_MIN_WAGE_DEMAND = 1000
HOUSEHOLD_RESERVATION_PRICE_BASE = 500
HOUSEHOLD_NEED_PRICE_MULTIPLIER = 1.0
HOUSEHOLD_ASSET_PRICE_MULTIPLIER = 0.1
HOUSEHOLD_PRICE_ELASTICITY_FACTOR = 0.5
HOUSEHOLD_STOCKPILING_BONUS_FACTOR = 0.2
MIN_SELL_PRICE = 100
MAX_SELL_PRICE = 10000
MAX_SELL_QUANTITY = 50.0
PERCEIVED_PRICE_UPDATE_FACTOR = 0.1
INVENTORY_HOLDING_COST_RATE = 0.005
DIVIDEND_RATE = 0.1  # 기본 배당률
DIVIDEND_RATE_MIN = 0.05  # 최소 배당률 (저배당 정책)
DIVIDEND_RATE_MAX = 0.5   # 최대 배당률 (고배당 정책)
# WAGE_DECAY_RATE removed - Overwritten in Phase 21.6 section
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
BASE_DESIRE_GROWTH = 1.0
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
# TARGET_FOOD_BUFFER_QUANTITY is already defined above
SURVIVAL_BUDGET_ALLOCATION = 0.6  # Default 60% of budget for survival
FOOD_CONSUMPTION_UTILITY = 10.0   # Utility per unit of food
PERCEIVED_FAIR_PRICE_THRESHOLD_FACTOR = 0.9
SURVIVAL_NEED_CONSUMPTION_THRESHOLD = (
    50.0  # Consume earlier (when hungry > 50)
)
FOOD_CONSUMPTION_QUANTITY = 1.0  # Eat MORE to reduce hunger faster
FOOD_CONSUMPTION_MAX_PER_TICK = (
    20.0  # Allow binging
)
FOOD_PURCHASE_MAX_PER_TICK = (
    50.0  # Allow bulk buy
)
HOUSEHOLD_MAX_PURCHASE_QUANTITY = 5.0 # Max units per item per tick for bulk buying
HOUSEHOLD_FOOD_PRICE_ELASTICITY = (
    0.5  # Factor to adjust demand based on price deviation from average
)
HOUSEHOLD_FOOD_STOCKPILE_TARGET_TICKS = (
    5  # How many ticks worth of food a household aims to stockpile when prices are good
)
HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 2.0  # Increased for Genesis circulation (Jules tuning)
HOUSEHOLD_MIN_FOOD_INVENTORY_TICKS = (
    2  # Minimum number of ticks worth of food a household aims to keep in inventory
)

# --- Agent Lifecycle & Death ---
SURVIVAL_NEED_DEATH_THRESHOLD = 100.0
ASSETS_DEATH_THRESHOLD = -500.0 # Allow some depth before death (Credit/Debt survival)
HOUSEHOLD_DEATH_TURNS_THRESHOLD = 10 # Increase survival window (10 ticks = 2.4 days)
SURVIVAL_NEED_DEATH_TICKS_THRESHOLD = 10 # Phase 33 Social Component alignment
ASSETS_CLOSURE_THRESHOLD = 0.0
FIRM_CLOSURE_TURNS_THRESHOLD = 20

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

# --- Genesis: Activation Energy (WO-047: Capital Injection) ---
INITIAL_HOUSEHOLD_ASSETS_MEAN = 500000  # 50.0 -> 5000.0 (100x Booster) -> Pennies
INITIAL_FIRM_CAPITAL_MEAN = 5000000   # 1000.0 -> 50000.0 (50x Runway for Regulations) -> Pennies

# --- Genesis: Market Flexibility Multipliers ---
GENESIS_PRICE_ADJUSTMENT_MULTIPLIER = 2.0  # Speed up price slashing
GENESIS_WAGE_FLEXIBILITY_FACTOR = 0.5      # How much faster households drop reservation wage

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
HALO_EFFECT = 0.15                # 학벌 프리미엄 (15% per Level)
EDUCATION_WEALTH_THRESHOLDS = {   # 자산별 시작 교육 수준
    0: 0.0,
    1: 2000.0,
    2: 5000.0,
    3: 10000.0,
    4: 20000.0,
    5: 50000.0
}


# --- Loan Market (Deprecated/Legacy - overwritten by Banking below) ---
LOAN_INTEREST_RATE = 0.05
INITIAL_BANK_ASSETS = 1000000.0
HOUSEHOLD_LOAN_THRESHOLD = 500.0
LOAN_DURATION = 20
DEFAULT_LOAN_DURATION = 10

# --- Banking & Time Scale (Phase 3) ---
TICKS_PER_YEAR = 100.0          # 1년 = 100틱 (모든 이자 계산의 기준)
INITIAL_BASE_ANNUAL_RATE = 0.05 # 연 5% (틱당 금리가 아님!)
DEFAULT_MORTGAGE_RATE = 0.05    # Default mortgage rate
LOAN_DEFAULT_TERM = 50          # 6개월 (50틱)
CREDIT_SPREAD_BASE = 0.02       # 연 2% 가산금리
DEFAULT_LOAN_SPREAD = 0.02      # WO-146 Alias for CREDIT_SPREAD_BASE
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
GOD_MODE_TOKEN = os.getenv("GOD_MODE_TOKEN", "default-god-token")



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
HOUSEHOLD_LOW_ASSET_THRESHOLD = 10000  # 자산이 이 값 미만이면 낮은 임금 수용
HOUSEHOLD_LOW_ASSET_WAGE = 800         # 자산이 낮을 때 희망 임금
HOUSEHOLD_DEFAULT_WAGE = 1000          # 기본 희망 임금

# 시장 가격 폴백 (시장 데이터 없을 때 사용)
MARKET_PRICE_FALLBACK = 1000
DEFAULT_FALLBACK_PRICE = 500
DEFAULT_FOOD_PRICE_ESTIMATE = 500 # MIGRATION: Int pennies (Default estimate for food)

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
AI_MIN_PRICE_FLOOR = 10            # AI가 설정 가능한 최저 가격 하한

# ------------------------------------------------------------------------------
# 📈 STOCK MARKET PARAMETERS (주식 시장 파라미터)
# ------------------------------------------------------------------------------
# 주식 시장 운영에 필요한 설정값들

# --- 기본 설정 ---
STOCK_MARKET_ENABLED = True         # 주식 시장 활성화 여부
STOCK_PRICE_LIMIT_RATE = 0.15       # 일일 가격 변동폭 제한 (±15%) Circuit Breaker

# --- 주가 결정 방식 ---
STOCK_PRICE_METHOD = "book_value"   # "book_value" 또는 "market_price"
STOCK_BOOK_VALUE_MULTIPLIER = 1.0   # 순자산가치 대비 기준 주가 배수 (PBR)

# --- 거래 관련 ---
STOCK_MIN_ORDER_QUANTITY = 1.0      # 최소 주문 수량
STOCK_ORDER_EXPIRY_TICKS = 5        # 주문 유효 기간 (틱)
STOCK_TRANSACTION_FEE_RATE = 0.001  # 거래 수수료율 (0.1%)

# --- 투자 의사결정 ---
HOUSEHOLD_INVESTMENT_BUDGET_RATIO = 0.2  # 자산 대비 최대 투자 비율
HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT = 50000  # 투자를 위한 최소 자산
STOCK_SELL_PROFIT_THRESHOLD = 0.15  # 매도 고려 수익률 임계값 (15%)
STOCK_BUY_DISCOUNT_THRESHOLD = 0.10 # 매수 고려 할인율 임계값 (10%)
STOCK_INVESTMENT_DIVERSIFICATION_COUNT = 3 # Number of stocks to diversify into
STOCK_INVESTMENT_EQUITY_DELTA_THRESHOLD = 10.0 # Threshold for buy/sell decisions based on portfolio optimization

# --- Phase 28: Macro-Stability Stress Testing (Config) ---
PANIC_SELLING_ASSET_THRESHOLD = 50000  # 자산이 이 값 미만이면 주식 패닉 셀링 (생존 위협)
DEBT_REPAYMENT_RATIO = 0.5             # 부채 상환 시 자산 대비 할당 비율 (기본 50%)
DEBT_REPAYMENT_CAP = 1.1               # 부채 상환 상한선 (원금 * 1.1)
DEBT_LIQUIDITY_RATIO = 0.9             # 부채 상환 후 최소 유동성 유지 비율 (자산의 90%까지만 상환)
DEFAULT_INFLATION_RATE = 0.02          # 기본 인플레이션율 (2%)

# --- IPO / SEO ---
IPO_INITIAL_SHARES = 1000.0
SEO_TRIGGER_RATIO = 0.5              # Trigger SEO when assets < STARTUP_COST * ratio
SEO_MAX_SELL_RATIO = 0.10            # Max 10% of treasury per tick

# --- Phase 3.1: Government & Taxation ---
INCOME_TAX_RATE = 0.0                 # Laissez-Faire: Zero Tax
INCOME_TAX_PAYER = "HOUSEHOLD"
CORPORATE_TAX_RATE = 0.0              # Laissez-Faire: Zero Tax
SALES_TAX_RATE = 0.0                 # Laissez-Faire: Zero Tax
INHERITANCE_TAX_RATE = 0.0            # Laissez-Faire: Zero Tax

RD_SUBSIDY_RATE = 0.2                 # R&D(자본투자) 보조금 (투자액의 20%)
INFRASTRUCTURE_INVESTMENT_COST = 500000  # 인프라 투자 1회당 비용
INFRASTRUCTURE_TFP_BOOST = 0.05       # 인프라 투자 시 전체 생산성(TFP) 증가율

# --- 배당 관련 (기존 DIVIDEND_RATE 참조) ---
# DIVIDEND_RATE는 이미 위에서 정의됨

# --- 창업 관련 ---
STARTUP_MIN_CAPITAL = 500000        # 창업 최소 자본금
STARTUP_INITIAL_SHARES = 100.0      # 창업 시 발행 주식 수
STARTUP_PROBABILITY = 0.01          # 틱당 창업 시도 확률 (자격 충족 시)

# --- Mitosis Configuration ---
TARGET_POPULATION = 50
MITOSIS_BASE_THRESHOLD = 250000  # 기본 분열 자산 요건 (5000.0 -> 2500.0 for Take 2)
MITOSIS_SENSITIVITY = 1.5       # 인구 압박 민감도
MITOSIS_SURVIVAL_THRESHOLD = 20.0  # 배고픔 한계
MITOSIS_MUTATION_PROBABILITY = 0.2  # 성격 돌연변이 확률
MITOSIS_Q_TABLE_MUTATION_RATE = 0.05  # Q-table 노이즈 비율

# --- Phase 4: Fiscal Policy ---

# --- Phase 7: Adaptive Fiscal Policy ---
DEFICIT_SPENDING_ENABLED = True
DEFICIT_SPENDING_LIMIT_RATIO = 0.30     # Max Debt / GDP Ratio
EMERGENCY_BUDGET_MULTIPLIER_CAP = 2.0   # 2.0x spending in crisis
NORMAL_BUDGET_MULTIPLIER_CAP = 1.0      # 1.0x spending in normal times
GOV_ACTION_INTERVAL = 30                # Actuator silent interval
FISCAL_SENSITIVITY_ALPHA = 0.5          # Output gap -> fiscal stance conversion
POTENTIAL_GDP_WINDOW = 50               # Ticks for moving average
TAX_RATE_MIN = 0.05
TAX_RATE_MAX = 0.50
TAX_RATE_BASE = 0.10                    # Neutral rate (boom/bust neutral)
BUDGET_ALLOCATION_MIN = 0.1
BUDGET_ALLOCATION_MAX = 1.0
DEBT_CEILING_RATIO = 2.0                # Max debt/GDP (Increased to 2.0 for stability)
FISCAL_STANCE_EXPANSION_THRESHOLD = 0.025   # +2.5% stance -> expand
FISCAL_STANCE_CONTRACTION_THRESHOLD = -0.025 # -2.5% stance -> contract

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
WEALTH_TAX_THRESHOLD = 5000000
ANNUAL_WEALTH_TAX_RATE = 0.02   # Annual 2% wealth tax

# 3. Welfare
# [PHASE 4] Re-enabling Welfare for Stabilization
UNEMPLOYMENT_BENEFIT_RATIO = 0.8 # 80% of survival cost
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
BRAND_RESILIENCE_FACTOR = 0.05    # Brand Awareness converts to resilience ticks

# 2. Consumer Behavior
QUALITY_SENSITIVITY_MEAN = 0.5    # Average preference for quality over price
BRAND_LOYALTY_DECAY = 0.95        # Loyalty score decays 5% per tick without reinforcement
NETWORK_EFFECT_WEIGHT = 0.5       # Weight of sales volume in Utility function
BRAND_SENSITIVITY_BETA = 0.5      # Consumer sensitivity to Brand Awareness
QUALITY_PREF_SNOB_MIN = 0.7       # Threshold for Snob behavior
QUALITY_PREF_MISER_MAX = 0.3      # Threshold for Miser behavior



# 3. AI Reward
# AI_VALUATION_MULTIPLIER = 1000.0   # Deprecated: Using relative asset valuation (5% of Assets * Delta Awareness)

# ==============================================================================
# Task #9: Entrepreneurship Constants
# ==============================================================================
MIN_FIRMS_THRESHOLD = 5          # 최소 기업 수 (이하로 떨어지면 창업 유도)
STARTUP_COST = 3000000           # 창업 비용 (30,000으로 상향)
FIRM_MAINTENANCE_FEE = 5000       # WO-021: 1/4 of legacy 200.0
CORPORATE_TAX_RATE = 0.0         # Laissez-Faire: Zero Tax
ENTREPRENEURSHIP_SPIRIT = 0.05   # 자격 있는 가계의 창업 확률 (5%)
STARTUP_CAPITAL_MULTIPLIER = 1.2 # 창업 자격: cash > STARTUP_COST * 이 값 (자격: 3600)

# ==============================================================================
# Phase 8: Inflation Psychology (Adaptive Expectations)
# ==============================================================================
INFLATION_MEMORY_WINDOW = 10     # Ticks to remember price history
PRICE_MEMORY_LENGTH = 10         # Length of price history deque (WO-095)
WAGE_MEMORY_LENGTH = 30          # Length of wage history deque (WO-095)
ADAPTATION_RATE_IMPULSIVE = 0.8  # Lambda for impulsive agents
ADAPTATION_RATE_NORMAL = 0.3     # Lambda for normal agents
ADAPTATION_RATE_CONSERVATIVE = 0.1 # Lambda for conservative agents

# ==============================================================================
# Phase 9: M&A & Bankruptcy Parameters
# ==============================================================================
MA_ENABLED = True
VALUATION_PER_MULTIPLIER = 10.0      # PER 10
MIN_ACQUISITION_CASH_RATIO = 1.5     # Hunter Cash >= Target Valuation * 1.5
LIQUIDATION_DISCOUNT_RATE = 0.5      # Asset fire sale discount
BANKRUPTCY_CONSECUTIVE_LOSS_TICKS = 20 # Warning threshold


PANIC_BUYING_THRESHOLD = 0.05    # Expected Inflation > 5% -> Hoard
HOARDING_FACTOR = 0.5            # Buy 50% more than needed

DEFLATION_WAIT_THRESHOLD = -0.05 # Expected Inflation < -5% -> Delay
DELAY_FACTOR = 0.5               # Buy 50% less than needed

# ==============================================================================
# Phase 10: Central Bank & Monetary Policy
# ==============================================================================
CB_UPDATE_INTERVAL = 10         # Central Bank policy update interval (ticks)
CB_INFLATION_TARGET = 0.02      # Target inflation rate (2%)
CB_TAYLOR_ALPHA = 1.5           # Taylor Rule weight on inflation
CB_TAYLOR_BETA = 0.5            # Taylor Rule weight on output gap

# --- Phase 4.5: Interest Sensitivity ---
NEUTRAL_REAL_RATE = 0.02
DSR_CRITICAL_THRESHOLD = 0.4
INTEREST_SENSITIVITY_ANT = 5.0
INTEREST_SENSITIVITY_GRASSHOPPER = 1.0

# --- Phase 6: Brand Marketing ROI Optimization ---
MARKETING_EFFICIENCY_HIGH_THRESHOLD = 1.5
MARKETING_EFFICIENCY_LOW_THRESHOLD = 0.8
MARKETING_BUDGET_RATE_MIN = 0.01
MARKETING_BUDGET_RATE_MAX = 0.20
BRAND_AWARENESS_SATURATION = 0.9
SERVICE_SECTORS = ["service.education", "service.medical"]
SERVICE_WASTE_PENALTY_FACTOR = 0.5

# ==============================================================================
# Phase 17-3A: Real Estate
# ==============================================================================
NUM_HOUSING_UNITS = 100
INITIAL_PROPERTY_VALUE = 1000000
INITIAL_RENT_PRICE = 10000
MAINTENANCE_RATE_PER_TICK = 0.001  # 0.1%
HOMELESS_PENALTY_PER_TICK = 5000

# ==============================================================================
# Phase 19: Population Dynamics
# ==============================================================================
REPRODUCTION_AGE_START = 20
REPRODUCTION_AGE_END = 45
CHILDCARE_TIME_REQUIRED = 8.0  # 자녀 1명당 하루 필요 시간
HOUSEWORK_BASE_HOURS = 6.0     # 가구 기본 가사 시간 (WO-035: 4~6 hours)
EDUCATION_COST_MULTIPLIERS = { # 교육 수준별 기대 임금 배수
    0: 1.0, 1: 1.5, 2: 2.2, 3: 3.5, 4: 5.0, 5: 8.0
}
SOCIAL_CAPILLARITY_COST = 0.5  # 계층 이동 비용 (K-Factor)
UNNAMED_CHILD_MORTALITY_RATE = 0.001 # 기본 사망률
EDUCATION_LEVEL_DISTRIBUTION = [0.4, 0.3, 0.15, 0.1, 0.04, 0.01] # 0~5단계 분포

# --- Phase 20: Socio-Tech & System 2 ---
# ==============================================================================
SYSTEM2_TICKS_PER_CALC = 10
SYSTEM2_HORIZON = 100
SYSTEM2_DISCOUNT_RATE = 0.98

FORMULA_TECH_LEVEL = 0.0   # 0.0: No Formula, 1.0: Full Formula
LACTATION_INTENSITY = 1.0  # Lock Factor (1.0 = Strong Lock)
HOMEWORK_QUALITY_COEFF = 0.5 # Impact of appliances

# --- Phase 21.5: Automation Tax ---
# --- WO-048: Adaptive Breeding Parameters ---
TECH_CONTRACEPTION_ENABLED = True   # True: System 2 (NPV), False: System 1 (Random)
BIOLOGICAL_FERTILITY_RATE = 0.15    # 피임 없을 때의 월간 임신 확률

# Cost Factors
CHILD_MONTHLY_COST = 50000          # 직접 양육비 (식비+교육비)
OPPORTUNITY_COST_FACTOR = 0.2       # 육아로 인한 임금 감소율 (0.3 -> 0.2 for Take 2)
RAISING_YEARS = 20                  # 양육 기간 (성인까지)

# Benefit Factors
CHILD_EMOTIONAL_VALUE_BASE = 50000000 # 자녀 1명당 느끼는 정서적 가치의 총량 (500k로 상향 - Middle Income Trap 완화)
OLD_AGE_SUPPORT_RATE = 0.1          # 자녀 소득의 10%를 노후 용돈으로 받음
SUPPORT_YEARS = 20                  # 은퇴 후 부양받는 기간

# --- Phase 23: Public Education System (WO-054) ---
PUBLIC_EDU_BUDGET_RATIO = 0.20  # 정부 예산의 20%를 교육에 투자
EDUCATION_COST_PER_LEVEL = {
    1: 50000,    # 기초 교육
    2: 200000,   # 중등 교육
    3: 500000,   # 고등 교육
    4: 1500000,  # 대학
    5: 5000000   # 대학원/전문직
}
SCHOLARSHIP_WEALTH_PERCENTILE = 0.20  # 하위 20%
SCHOLARSHIP_POTENTIAL_THRESHOLD = 0.7  # 잠재력 상위 30%

# --- WO-098-DIAG-C: Tech Adoption Barriers (Hotfix) ---
TECH_FERTILIZER_UNLOCK_TICK = 30  # Unlock earlier (Default 50 -> 30)
TECH_DIFFUSION_RATE = 0.10        # 2x faster adoption (Default 0.05 -> 0.10)

# --- Phase 24: Adaptive Evolution (WO-057) ---
GOVERNMENT_POLICY_MODE = "AI_ADAPTIVE"  # "TAYLOR_RULE" (WO-056) or "AI_ADAPTIVE" (WO-057)
TARGET_INFLATION_RATE = 0.02      # 2%
TARGET_UNEMPLOYMENT_RATE = 0.04   # 4%
GOV_ACTION_INTERVAL = 30          # 의사결정 주기 (30틱 = 1개월)
RL_LEARNING_RATE = 0.1
RL_DISCOUNT_FACTOR = 0.95

# ==============================================================================
# Phase 26: Macro-Linked Portfolio (WO-062)
# ==============================================================================
MACRO_PORTFOLIO_ADJUSTMENT_ENABLED = True
BAILOUT_REPAYMENT_RATIO = 0.5

# --- Newborn Configuration ---
NEWBORN_INITIAL_NEEDS = {
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
    "quality": 0.0,
}

# --- Missing Configuration Fields (Added by WO-135.1) ---
EXPECTED_STARTUP_ROI = 0.15
LABOR_ALPHA = 0.7
DIVIDEND_SUSPENSION_LOSS_TICKS = 3
AUTOMATION_TAX_RATE = 0.05
ALTMAN_Z_SCORE_THRESHOLD = 1.81
INVISIBLE_HAND_SENSITIVITY = 0.1
CAPITAL_TO_OUTPUT_RATIO = 2.0
FIRM_SAFETY_MARGIN = 200000

# --- Added for DTO Parity (WO-135.2) ---
CAPITAL_DEPRECIATION_RATE = 0.05
INITIAL_FIRM_LIQUIDITY_NEED = 20000
BANKRUPTCY_CONSECUTIVE_LOSS_THRESHOLD = 20
HOUSING_EXPECTATION_CAP = 0.05

# ==============================================================================
# WO-136: Tech Generalization & Market Safety
# ==============================================================================
MARKET_CIRCUIT_BREAKER_BASE_LIMIT = 0.15  # Base limit for market circuit breakers
TECH_UNLOCK_COST_THRESHOLD = 500000       # R&D Investment threshold for tech unlock
TECH_UNLOCK_PROB_CAP = 0.1                # Maximum probability per tick for tech unlock

# ==============================================================================
# WO-148: Stress Test Parameters
# ==============================================================================
STARVATION_THRESHOLD = 1.0  # Food inventory threshold for starvation metrics
PRIMARY_SURVIVAL_GOOD_ID = "basic_food" # Required by HouseholdConfigDTO
SURVIVAL_NEED_EMERGENCY_THRESHOLD = 80.0 # Threshold for emergency behavior
SURVIVAL_BID_PREMIUM = 20 # Premium paid for survival goods (Additive pennies)
FIRE_SALE_INVENTORY_TARGET = 0.5 # Inventory level to trigger fire sale
FIRE_SALE_PRICE_DISCOUNT = 0.2 # Discount during fire sale
DEFAULT_TARGET_MARGIN = 0.2 # Default target margin for firms
MAX_PRICE_STALENESS_TICKS = 10 # Ticks before price is considered stale
FIRE_SALE_INVENTORY_THRESHOLD = 0.5 # Threshold to start fire sale
FIRE_SALE_DISCOUNT = 0.2 # Discount for fire sale
FIRE_SALE_COST_DISCOUNT = 0.5 # Discount below cost for fire sale
FIRE_SALE_ASSET_THRESHOLD = 50000 # Asset threshold for fire sale

# ==============================================================================
# WO-157: Code Blue Implementation
# ==============================================================================
ELASTICITY_MAPPING = {
    "MISER": 2.0,
    "IMPULSIVE": 0.5,
    "STATUS_SEEKER": 1.0,
    "GROWTH_ORIENTED": 0.8,
    "CONSERVATIVE": 1.5,
    "DEFAULT": 1.0
}
MAX_WILLINGNESS_TO_PAY_MULTIPLIER = 2.5
SALE_TIMEOUT_TICKS = 20
DYNAMIC_PRICE_REDUCTION_FACTOR = 0.95

# ==============================================================================
# 🔧 Externalized Constants (Refactor 2026-02-03)
# ==============================================================================
# Bank & Finance
# TICKS_PER_YEAR and INITIAL_BASE_ANNUAL_RATE are already defined above.
DEFAULT_LOAN_TERM_TICKS = 50
BANK_DEPOSIT_MARGIN = 0.02
BANK_CREDIT_SPREAD_BASE = 0.02
# CREDIT_RECOVERY_TICKS is already defined as 100 in Phase 4 section, but reassuring.
# BANKRUPTCY_XP_PENALTY is already defined as 0.2.
BANK_SOLVENCY_BUFFER = 100000
DEFAULT_MORTGAGE_INTEREST_RATE = 0.05

# Agent Behavior
INITIAL_HOUSEHOLD_AGE_RANGE = (20.0, 60.0)
INITIAL_APTITUDE_DISTRIBUTION = (0.5, 0.15)
EMERGENCY_LIQUIDATION_DISCOUNT = 0.8
EMERGENCY_STOCK_LIQUIDATION_FALLBACK_PRICE = 800
DISTRESS_GRACE_PERIOD_TICKS = 5
BASE_LABOR_SKILL = 1.0

# AI
AI_EPSILON_DECAY_PARAMS = (0.5, 0.05, 700)
AI_REWARD_BRAND_VALUE_MULTIPLIER = 0.05
HOUSING_NPV_HORIZON_YEARS = 10
HOUSING_NPV_RISK_PREMIUM = 0.02
MORTGAGE_DEFAULT_DOWN_PAYMENT_RATE = 0.2

# System & Policy
FORECLOSURE_FIRE_SALE_DISCOUNT = 0.8
FRIENDLY_MERGER_PREMIUM = 1.1
HOSTILE_TAKEOVER_PREMIUM = 1.2
HOSTILE_TAKEOVER_SUCCESS_PROB = 0.6
MERGER_EMPLOYEE_RETENTION_RATES = (0.3, 0.5)
POLICY_ACTUATOR_STEP_SIZES = (0.01, 0.0025, 0.1)
POLICY_ACTUATOR_BOUNDS = {
    "tax": (0.05, 0.50),
    "rate": (0.0, 0.20),
    "budget": (0.1, 1.0)
}

# Misc
AGE_DEATH_PROBABILITIES = {
    60: 0.01,
    70: 0.02,
    80: 0.05,
    90: 0.15,
    100: 0.50
}
FALLBACK_SURVIVAL_COST = 1000
PRICE_VOLATILITY_WINDOW_TICKS = 20
HOUSING_ANNUAL_MAINTENANCE_RATE = 0.01
