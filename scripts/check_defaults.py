
import importlib.util
import sys
import os

# Import config/defaults.py
spec = importlib.util.spec_from_file_location("defaults", "config/defaults.py")
defaults = importlib.util.module_from_spec(spec)
spec.loader.exec_module(defaults)

monetary_keys = [
    "INITIAL_HOUSEHOLD_LIQUIDITY_NEED_MEAN",
    "INITIAL_FIRM_CAPITAL_MEAN",
    "INITIAL_FIRM_LIQUIDITY_NEED_MEAN",
    "HOUSEHOLD_LOW_ASSET_THRESHOLD",
    "HOUSEHOLD_LOW_ASSET_WAGE",
    "HOUSEHOLD_DEFAULT_WAGE",
    "MARKET_PRICE_FALLBACK",
    "DEFAULT_FALLBACK_PRICE",
    "INITIAL_WAGE",
    "BASE_WAGE",
    "LABOR_MARKET_MIN_WAGE",
    "HOUSEHOLD_MIN_WAGE_DEMAND",
    "HOUSEHOLD_RESERVATION_PRICE_BASE",
    "SURVIVAL_BID_PREMIUM"
]

errors = []
for key in monetary_keys:
    if hasattr(defaults, key):
        val = getattr(defaults, key)
        if not isinstance(val, int):
            errors.append(f"{key} is {type(val)}: {val} (Expected int)")
    else:
        errors.append(f"{key} missing in defaults.py")

# Check GOODS prices
if hasattr(defaults, "GOODS"):
    for good, data in defaults.GOODS.items():
        if "production_cost" in data and not isinstance(data["production_cost"], int):
             errors.append(f"GOODS[{good}]['production_cost'] is {type(data['production_cost'])} (Expected int)")
        if "initial_price" in data and not isinstance(data["initial_price"], int):
             errors.append(f"GOODS[{good}]['initial_price'] is {type(data['initial_price'])} (Expected int)")

if errors:
    print("ERRORS FOUND:")
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print("All monetary checks passed.")
