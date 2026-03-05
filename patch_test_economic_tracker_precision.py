import re

with open('tests/test_economic_tracker_precision.py', 'r') as f:
    content = f.read()

import_statement = "from modules.analytics.api import EconomyAnalyticsSnapshotDTO, HouseholdAnalyticsDTO, FirmAnalyticsDTO, MarketAnalyticsDTO\n"

if import_statement not in content:
    content = content.replace("from simulation.metrics.economic_tracker import EconomicIndicatorTracker", f"from simulation.metrics.economic_tracker import EconomicIndicatorTracker\n{import_statement}")


track_block = r'''        self.tracker.track(
            time=1,
            households=[h1, h2],
            firms=[f1, f2],
            markets={'food_market': m1},
            money_supply=210.0,
            m2_leak=0.0
        )'''

replacement = r'''        # Construct DTOs
        h1_dto = HouseholdAnalyticsDTO(
            agent_id=1,
            is_active=True,
            total_cash_pennies=10000,
            portfolio_value_pennies=0,
            is_employed=True,
            trust_score=0.5,
            survival_need=0.5,
            consumption_expenditure_pennies=555,
            food_expenditure_pennies=333,
            labor_income_pennies=1200,
            education_level=1.0,
            aptitude=1.0
        )

        h2_dto = HouseholdAnalyticsDTO(
            agent_id=2,
            is_active=True,
            total_cash_pennies=5000,
            portfolio_value_pennies=0,
            is_employed=False,
            trust_score=0.5,
            survival_need=0.5,
            consumption_expenditure_pennies=100,
            food_expenditure_pennies=50,
            labor_income_pennies=0,
            education_level=1.0,
            aptitude=1.0
        )

        f1_dto = FirmAnalyticsDTO(
            agent_id=1,
            is_active=True,
            total_assets_pennies=20000,
            cash_balance_pennies=20000,
            current_production=100.0,
            inventory_volume=50.0,
            sales_volume=80.0
        )

        f2_dto = FirmAnalyticsDTO(
            agent_id=2,
            is_active=True,
            total_assets_pennies=30000,
            cash_balance_pennies=15000, # with 15000 non-cash assets = 30000 total
            current_production=50.0,
            inventory_volume=20.0,
            sales_volume=40.0
        )

        m1_dto = MarketAnalyticsDTO(
            market_id="food_market",
            avg_price=2.5,
            volume=100.0,
            current_price=2.5
        )

        snapshot = EconomyAnalyticsSnapshotDTO(
            tick=1,
            households=[h1_dto, h2_dto],
            firms=[f1_dto, f2_dto],
            markets=[m1_dto],
            money_supply_pennies=21000,
            m2_leak_pennies=0,
            monetary_base_pennies=0
        )

        self.tracker.track_tick(snapshot)'''

content = content.replace(track_block, replacement)

with open('tests/test_economic_tracker_precision.py', 'w') as f:
    f.write(content)
