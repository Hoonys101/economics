with open("modules/household/engines/budget.py", "r") as f:
    content = f.read()

content = content.replace(
    "avg_market_wage_float = market_snapshot.labor.avg_wage if hasattr(market_snapshot, 'labor') else 0.0",
    "avg_market_wage_float = market_snapshot.labor.avg_wage if getattr(market_snapshot, 'labor', None) is not None else 0.0"
)

content = content.replace(
    "min_wage = config.household_min_wage_demand if hasattr(config, 'household_min_wage_demand') else 0",
    "min_wage = getattr(config, 'household_min_wage_demand', 0)"
)

content = content.replace(
    "housing_snap = market_snapshot.housing if hasattr(market_snapshot, 'housing') else None",
    "housing_snap = getattr(market_snapshot, 'housing', None)"
)

with open("modules/household/engines/budget.py", "w") as f:
    f.write(content)
