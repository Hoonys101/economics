from unittest.mock import MagicMock
from modules.government.api import IGovernment
from simulation.agents.government import Government
from modules.government.dtos import FiscalPolicyDTO
from modules.system.api import DEFAULT_CURRENCY
import typing

print("--- No Spec ---")
mock_gov_ns = MagicMock()
mock_gov_ns.corporate_tax_rate = 0.2
mock_gov_ns.income_tax_rate = 0.1
mock_gov_ns.fiscal_policy = MagicMock(spec=FiscalPolicyDTO)
mock_gov_ns.expenditure_this_tick = {DEFAULT_CURRENCY: 0}
mock_gov_ns.revenue_this_tick = {DEFAULT_CURRENCY: 0}
mock_gov_ns.total_debt = 0
mock_gov_ns.total_wealth = 0
mock_gov_ns.state = MagicMock()
mock_gov_ns.make_policy_decision = MagicMock()
# Added new fields
mock_gov_ns.id = 1
mock_gov_ns.name = "Gov"
mock_gov_ns.is_active = True

required = ["expenditure_this_tick", "revenue_this_tick", "total_debt", "total_wealth", "state", "make_policy_decision", "corporate_tax_rate", "income_tax_rate", "fiscal_policy", "id", "name", "is_active"]
for attr in required:
    has = hasattr(mock_gov_ns, attr)
    print(f"Mock has {attr}: {has}")

print(f"Is instance: {isinstance(mock_gov_ns, IGovernment)}")
