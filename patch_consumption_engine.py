with open("modules/household/engines/consumption_engine.py", "r") as f:
    content = f.read()

# Add comment above assets_val < threshold
old_comment = "assets_val = new_econ_state.wallet.get_balance(DEFAULT_CURRENCY)"
new_comment = "# assets_val and threshold are both evaluated in integer pennies.\n            assets_val = new_econ_state.wallet.get_balance(DEFAULT_CURRENCY)"
content = content.replace(old_comment, new_comment)

# Replace hasattr(order, 'item_id') with getattr(order, 'item_id', None) is not None
content = content.replace(
    "hasattr(order, 'item_id')",
    "getattr(order, 'item_id', None) is not None"
)

with open("modules/household/engines/consumption_engine.py", "w") as f:
    f.write(content)
