with open("modules/household/mixins/_state_access.py", "r") as f:
    content = f.read()

content = content.replace(
    "if loan_market and hasattr(loan_market, 'bank'):",
    "if loan_market and getattr(loan_market, 'bank', None) is not None:"
)

with open("modules/household/mixins/_state_access.py", "w") as f:
    f.write(content)
