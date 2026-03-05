import re

with open('tests/integration/test_reporting_pennies.py', 'r') as f:
    content = f.read()

import_statement = "from modules.analytics.api import EconomyAnalyticsSnapshotDTO, HouseholdAnalyticsDTO, FirmAnalyticsDTO, MarketAnalyticsDTO\n"

if import_statement not in content:
    content = content.replace("from simulation.metrics.economic_tracker import EconomicIndicatorTracker", f"from simulation.metrics.economic_tracker import EconomicIndicatorTracker\n{import_statement}")


track_block = r'''        tracker.track(1, households, firms, markets)'''

replacement = r'''        # Create DTOs
        h_dto = HouseholdAnalyticsDTO(
            agent_id=1,
            is_active=True,
            total_cash_pennies=0,
            portfolio_value_pennies=0,
            is_employed=False,
            trust_score=0.5,
            survival_need=0.5,
            consumption_expenditure_pennies=1000,
            food_expenditure_pennies=0,
            labor_income_pennies=0,
            education_level=1.0,
            aptitude=0.5
        )
        snapshot = EconomyAnalyticsSnapshotDTO(
            tick=1,
            households=[h_dto],
            firms=[],
            markets=[],
            money_supply_pennies=0,
            m2_leak_pennies=0,
            monetary_base_pennies=0
        )
        tracker.track_tick(snapshot)'''

content = content.replace(track_block, replacement)

with open('tests/integration/test_reporting_pennies.py', 'w') as f:
    f.write(content)
