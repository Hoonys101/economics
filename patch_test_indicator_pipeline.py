import re

with open('tests/integration/scenarios/diagnosis/test_indicator_pipeline.py', 'r') as f:
    content = f.read()

import_statement = "from modules.analytics.api import EconomyAnalyticsSnapshotDTO, HouseholdAnalyticsDTO, FirmAnalyticsDTO, MarketAnalyticsDTO\n"

if import_statement not in content:
    content = content.replace("from simulation.metrics.economic_tracker import EconomicIndicatorTracker", f"from simulation.metrics.economic_tracker import EconomicIndicatorTracker\n{import_statement}")

track_block = r'''    tracker.track(
        time=1,
        households=[],
        firms=[],
        markets={},
        money_supply=0.0,
        m2_leak=0.0,
        monetary_base=0.0
    )'''

replacement = r'''    # Construct DTOs
    snapshot = EconomyAnalyticsSnapshotDTO(
        tick=1,
        households=[],
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
