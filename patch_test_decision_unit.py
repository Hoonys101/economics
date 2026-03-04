with open("tests/unit/modules/household/test_decision_unit.py", "r") as f:
    content = f.read()

content = content.replace(
    "mock_housing_system = MagicMock()",
    "from modules.household.connectors.housing_connector import IHousingSystem\n        mock_housing_system = MagicMock(spec=IHousingSystem)"
)

with open("tests/unit/modules/household/test_decision_unit.py", "w") as f:
    f.write(content)
