import re

with open('tests/integration/test_reporting_pennies.py', 'r') as f:
    content = f.read()

dto_block = r'''        # Create DTOs
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
        )'''

replacement = r'''        # Create DTOs
        h_dto = HouseholdAnalyticsDTO(
            agent_id=1,
            is_active=True,
            total_cash_pennies=0,
            portfolio_value_pennies=0,
            is_employed=False,
            trust_score=0.5,
            survival_need=0.5,
            consumption_expenditure_pennies=5000,
            food_expenditure_pennies=2000,
            labor_income_pennies=0,
            education_level=1.0,
            aptitude=0.5
        )'''

content = content.replace(dto_block, replacement)

with open('tests/integration/test_reporting_pennies.py', 'w') as f:
    f.write(content)
