import re

with open('tests/unit/test_metrics_hardening.py', 'r') as f:
    content = f.read()

track_block = r'''        # Execute track
        tracker.track(
            time=1,
            households=[h1, h2],
            firms=[f1],
            markets=markets,
            money_supply=100000.0,
            m2_leak=0.0,
            monetary_base=50000.0
        )'''

replacement = r'''        # Execute track
        # Construct DTOs
        h1_dto = HouseholdAnalyticsDTO(
            agent_id=1,
            is_active=True,
            total_cash_pennies=1000,
            portfolio_value_pennies=0,
            is_employed=True,
            trust_score=0.5,
            survival_need=0.5,
            consumption_expenditure_pennies=500,
            food_expenditure_pennies=200,
            labor_income_pennies=1000,
            education_level=1,
            aptitude=0.5
        )

        h2_dto = HouseholdAnalyticsDTO(
            agent_id=2,
            is_active=True,
            total_cash_pennies=2000,
            portfolio_value_pennies=0,
            is_employed=False,
            trust_score=0.6,
            survival_need=0.5,
            consumption_expenditure_pennies=100,
            food_expenditure_pennies=50,
            labor_income_pennies=0,
            education_level=2,
            aptitude=0.9
        )

        f1_dto = FirmAnalyticsDTO(
            agent_id=1,
            is_active=True,
            total_assets_pennies=10000,
            cash_balance_pennies=10000,
            current_production=10.0,
            inventory_volume=50.0,
            sales_volume=5.0
        )

        m1_dto = MarketAnalyticsDTO(
            market_id="goods_market",
            avg_price=10.0,
            volume=100.0,
            current_price=10.0
        )

        snapshot = EconomyAnalyticsSnapshotDTO(
            tick=1,
            households=[h1_dto, h2_dto],
            firms=[f1_dto],
            markets=[m1_dto],
            money_supply_pennies=10000000,
            m2_leak_pennies=0,
            monetary_base_pennies=5000000
        )

        tracker.track_tick(snapshot)'''

content = content.replace(track_block, replacement)

with open('tests/unit/test_metrics_hardening.py', 'w') as f:
    f.write(content)
