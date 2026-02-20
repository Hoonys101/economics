# Firm Architecture Constants
# Extracted for Decoupling Mission (firm-decoupling)

# Market Insight
DEFAULT_MARKET_INSIGHT = 0.5
INSIGHT_DECAY_RATE = 0.001
INSIGHT_BOOST_FACTOR = 0.05
INSIGHT_ERROR_THRESHOLD = 1000.0  # Threshold for TD-Error boost (pennies)

# Marketing
DEFAULT_MARKETING_BUDGET_RATE = 0.05

# Liquidation & Valuation
DEFAULT_LIQUIDATION_PRICE = 1000
DEFAULT_PRICE = 1000  # Default price in pennies if not found
DEFAULT_INVENTORY_VALUATION_PRICE = 1000

# Labor & HR
DEFAULT_LABOR_WAGE = 1000  # Default wage in pennies
DEFAULT_SURVIVAL_COST = 10.0
DEFAULT_SEVERANCE_WEEKS = 2.0
TICKS_PER_YEAR = 365

# Taxes
DEFAULT_CORPORATE_TAX_RATE = 0.2

# Production
PRODUCTIVITY_DIVIDER = 10.0  # Used in Brand Update for productivity factor normalization
