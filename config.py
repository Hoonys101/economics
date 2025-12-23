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
INITIAL_HOUSEHOLD_ASSETS_MEAN = 50.0
INITIAL_HOUSEHOLD_ASSETS_RANGE = 0.2
INITIAL_HOUSEHOLD_LIQUIDITY_NEED_MEAN = 50.0
INITIAL_HOUSEHOLD_LIQUIDITY_NEED_RANGE = 0.2
INITIAL_HOUSEHOLD_NEEDS_MEAN = {
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
    "basic_food": {"production_cost": 3, "utility_effects": {"survival": 10}},
    "luxury_food": {
        "production_cost": 10,
        "utility_effects": {"survival": 12, "social": 5},
    },
}


# --- Firm Specialization ---
# Assigns which firms produce which goods. Assumes NUM_FIRMS = 4
FIRM_SPECIALIZATIONS = {
    0: "basic_food",
    1: "basic_food",
    2: "luxury_food",
    3: "luxury_food",
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
DIVIDEND_RATE = 0.1
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

# --- Loan Market ---
LOAN_INTEREST_RATE = 0.05
INITIAL_BANK_ASSETS = 1000000.0
HOUSEHOLD_LOAN_THRESHOLD = 500.0
LOAN_DURATION = 20
DEFAULT_LOAN_DURATION = 10

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
