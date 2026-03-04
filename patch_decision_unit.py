import re

with open("modules/household/decision_unit.py", "r") as f:
    content = f.read()

# Add import
import_stmt = "from modules.household.connectors.housing_connector import IHousingSystem\n"
if "IHousingSystem" not in content:
    content = content.replace("from modules.household.dtos import EconStateDTO", "from modules.household.dtos import EconStateDTO\n" + import_stmt)

# Replace hasattr with isinstance
content = content.replace(
    "if housing_system and hasattr(housing_system, 'initiate_purchase'):",
    "if housing_system and isinstance(housing_system, IHousingSystem):"
)

# Add comment above assets_val < threshold
old_comment = "# Fix: Use wallet balance."
new_comment = "# Fix: Use wallet balance.\n            # assets_val and threshold are both evaluated in integer pennies."
content = content.replace(old_comment, new_comment)

# Replace hasattr(order, 'item_id') with getattr(order, 'item_id', None) is not None
content = content.replace(
    "hasattr(order, 'item_id')",
    "getattr(order, 'item_id', None) is not None"
)

with open("modules/household/decision_unit.py", "w") as f:
    f.write(content)
