import re

with open('tests/integration/test_wo058_production.py', 'r') as f:
    content = f.read()

import_statement = "from modules.analytics.api import EconomyAnalyticsSnapshotDTO, HouseholdAnalyticsDTO, FirmAnalyticsDTO, MarketAnalyticsDTO\n"

if import_statement not in content:
    content = content.replace("from simulation.metrics.economic_tracker import EconomicIndicatorTracker", f"from simulation.metrics.economic_tracker import EconomicIndicatorTracker\n{import_statement}")


track_block = r'''    sim.tracker.track(1, sim.households, sim.firms, sim.markets, 0)'''

replacement = r'''    # Create DTOs for tracker manually or run phase 6
    household_dtos = []
    for h in sim.households:
        household_dtos.append(HouseholdAnalyticsDTO(
            agent_id=h.id,
            is_active=h._bio_state.is_active,
            total_cash_pennies=1000,
            portfolio_value_pennies=0,
            is_employed=True,
            trust_score=0.5,
            survival_need=0.5,
            consumption_expenditure_pennies=0,
            food_expenditure_pennies=0,
            labor_income_pennies=0,
            education_level=1.0,
            aptitude=0.5
        ))

    firm_dtos = []
    for f in sim.firms:
        firm_dtos.append(FirmAnalyticsDTO(
            agent_id=f.id,
            is_active=getattr(f, "is_active", False),
            total_assets_pennies=1000,
            cash_balance_pennies=1000,
            current_production=getattr(f, "current_production", 0.0),
            inventory_volume=sum(f.get_all_items().values()) if hasattr(f, "get_all_items") and f.get_all_items() else 0.0,
            sales_volume=getattr(f, "sales_volume_this_tick", 0.0)
        ))

    snapshot = EconomyAnalyticsSnapshotDTO(
        tick=1,
        households=household_dtos,
        firms=firm_dtos,
        markets=[],
        money_supply_pennies=0,
        m2_leak_pennies=0,
        monetary_base_pennies=0
    )
    sim.tracker.track_tick(snapshot)'''

content = content.replace(track_block, replacement)

with open('tests/integration/test_wo058_production.py', 'w') as f:
    f.write(content)
