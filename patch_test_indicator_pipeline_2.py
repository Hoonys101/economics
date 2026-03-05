import re

with open('tests/integration/scenarios/diagnosis/test_indicator_pipeline.py', 'r') as f:
    content = f.read()

track_block = r'''    # Act
    # track(self, time: int, households: List[Household], firms: List[Firm], markets: Dict[str, Market])
    tracker.track(
        time=1,
        households=[simple_household],
        firms=[],
        markets={}
    )'''

replacement = r'''    # Act
    # Create DTO
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

with open('tests/integration/scenarios/diagnosis/test_indicator_pipeline.py', 'w') as f:
    f.write(content)
