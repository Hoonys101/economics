with open("modules/household/engines/social.py", "r") as f:
    content = f.read()

content = content.replace(
    'elif hasattr(gov_data, "party"):',
    'elif getattr(gov_data, "party", None) is not None:'
)

with open("modules/household/engines/social.py", "w") as f:
    f.write(content)
