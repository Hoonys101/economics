import re

for filename in ["modules/household/econ_component.py", "modules/household/engines/belief_engine.py"]:
    with open(filename, "r") as f:
        content = f.read()

    content = content.replace(
        'hasattr(stress_scenario_config, "inflation_expectation_multiplier")',
        'getattr(stress_scenario_config, "inflation_expectation_multiplier", None) is not None'
    )

    with open(filename, "w") as f:
        f.write(content)
