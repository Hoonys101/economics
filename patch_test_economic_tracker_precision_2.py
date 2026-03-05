import re

with open('tests/test_economic_tracker_precision.py', 'r') as f:
    content = f.read()

track_block = r'''        # Run track
        self.tracker.track(
            time=1,
            households=[h1],
            firms=[f1],
            markets=markets,
            money_supply=100000.0,
            m2_leak=0.0,
            monetary_base=50000.0
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
            consumption_expenditure_pennies=5000,
            food_expenditure_pennies=2000,
            labor_income_pennies=3000,
            education_level=1.0,
            aptitude=0.5
        )

        f1_dto = FirmAnalyticsDTO(
            agent_id=1,
            is_active=True,
            total_assets_pennies=20000,
            cash_balance_pennies=20000,
            current_production=10.0,
            inventory_volume=10.0,
            sales_volume=5.0
        )

        m1_dto = MarketAnalyticsDTO(
            market_id="goods",
            avg_price=100.0,
            volume=10.0,
            current_price=100.0
        )

        snapshot = EconomyAnalyticsSnapshotDTO(
            tick=1,
            households=[h1_dto],
            firms=[f1_dto],
            markets=[m1_dto],
            money_supply_pennies=10000000,
            m2_leak_pennies=0,
            monetary_base_pennies=5000000
        )

        self.tracker.track_tick(snapshot)'''

content = content.replace(track_block, replacement)

with open('tests/test_economic_tracker_precision.py', 'w') as f:
    f.write(content)
