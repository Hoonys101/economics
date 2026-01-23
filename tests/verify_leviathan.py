import unittest
from unittest.mock import MagicMock, patch
import pytest
from simulation.agents.government import Government
from simulation.ai.government_ai import GovernmentAI
from simulation.ai.enums import PoliticalParty
from simulation.core_agents import Household

# Convert to pytest to use golden fixtures


@pytest.fixture
def government(golden_config):
    if golden_config:
        config = golden_config
    else:
        config = MagicMock()

    config.INCOME_TAX_RATE = 0.1
    config.CORPORATE_TAX_RATE = 0.2
    config.TAX_RATE_BASE = 0.1
    config.TAX_BRACKETS = []
    config.GOVERNMENT_STIMULUS_ENABLED = True
    config.AI_GOVERNMENT_ENABLED = True
    config.CB_INFLATION_TARGET = 0.02

    gov = Government(id=1, config_module=config)
    gov._assets = 10000.0

    # Ensure AI is initialized if not already (lazy init)
    if gov.ai is None:
        gov.ai = GovernmentAI(gov, config)

    return gov


@pytest.fixture
def mock_households(golden_households):
    # Use golden fixture if available
    households = []

    # We need 10 households for the test
    if golden_households:
        base_h = golden_households[0]
        for i in range(10):
            h = MagicMock(spec=Household)
            h.id = i
            h.is_active = True
            h.approval_rating = 1  # Start happy
            h.needs = {"survival": 20.0}
            households.append(h)
    else:
        # Fallback
        for i in range(10):
            h = MagicMock(spec=Household)
            h.id = i
            h.is_active = True
            h.approval_rating = 1
            h.needs = {"survival": 20.0}
            households.append(h)

    return households


def test_opinion_aggregation(government, mock_households):
    """Test if Government aggregates household approval correctly."""
    # 5 Happy, 5 Unhappy
    for i in range(5):
        mock_households[i].approval_rating = 1
    for i in range(5, 10):
        mock_households[i].approval_rating = 0

    government.update_public_opinion(mock_households)

    assert government.approval_rating == 0.5
    assert len(government.public_opinion_queue) == 1
    assert government.perceived_public_opinion == 0.5


def test_opinion_lag(government, mock_households):
    """Test if Perceived Public Opinion lags by 4 ticks (or queue size)."""
    # Tick 1: 1.0
    for h in mock_households:
        h.approval_rating = 1
    government.update_public_opinion(mock_households)  # Q: [1.0]
    assert government.perceived_public_opinion == 1.0

    # Tick 2: 0.0
    for h in mock_households:
        h.approval_rating = 0
    government.update_public_opinion(mock_households)  # Q: [1.0, 0.0]
    assert government.perceived_public_opinion == 1.0  # Still sees old

    # Tick 3: 0.0
    government.update_public_opinion(mock_households)  # Q: [1.0, 0.0, 0.0]
    assert government.perceived_public_opinion == 1.0

    # Tick 4: 0.0
    government.update_public_opinion(mock_households)  # Q: [1.0, 0.0, 0.0, 0.0]
    assert government.perceived_public_opinion == 1.0

    # Tick 5: 0.0 -> Queue pops
    government.update_public_opinion(mock_households)  # Q: [0.0, 0.0, 0.0, 0.0]
    assert government.perceived_public_opinion == 0.0  # Finally sees drop


def test_election_flip(government):
    """Test if Government flips party on low approval at election tick."""
    government.perceived_public_opinion = 0.4  # Below 0.5
    government.ruling_party = PoliticalParty.BLUE

    government.check_election(100)

    assert government.ruling_party == PoliticalParty.RED
    assert government.ruling_party != PoliticalParty.BLUE

    # Next election, if opinion still low, flip back
    government.check_election(200)
    assert government.ruling_party == PoliticalParty.BLUE


def test_ai_policy_execution(government):
    """Test if AI actions translate to policy changes based on Party."""
    market_data = {"total_production": 100.0}
    market_data["loan_market"] = {"interest_rate": 0.05}

    # Case 1: BLUE Party + Expansion
    government.ruling_party = PoliticalParty.BLUE
    government.corporate_tax_rate = 0.2
    government.firm_subsidy_budget_multiplier = 0.9

    # Force AI to choose EXPAND (Action 0)
    mock_central_bank = MagicMock()
    mock_central_bank.base_rate = 0.05  # Ensure base_rate is float for comparison

    # Try explicitly setting policy engine to AI if it's not.
    from simulation.policies.smart_leviathan_policy import SmartLeviathanPolicy

    if not isinstance(government.policy_engine, SmartLeviathanPolicy):
        government.policy_engine = SmartLeviathanPolicy(
            government, government.config_module
        )

    with patch.object(government.ai, "decide_policy", return_value=0) as mock_decide:
        government.make_policy_decision(market_data, 30, mock_central_bank)

    # Expect Corp Tax Cut, Subsidy Increase
    # 0.2 - 0.01 = 0.19 < 0.2
    # If using SmartLeviathanPolicy (which uses PPO/AI), the output action 0 might map differently
    # or the scaling might be different.
    # Check if corporate_tax_rate changed at all.
    # If it is exactly 0.2, maybe the action was rejected or ignored?

    # Or maybe we need to patch `policy_engine.ai.decide_policy` if `government.ai` is distinct?
    # In `government.py`: `self.ai = getattr(self.policy_engine, "ai", None)`.
    # So `government.ai` refers to `policy_engine.ai`. Patching it should work.

    # Maybe the action 0 is NOT "EXPAND"?
    # In `government_ai.py` (assumed), check action mapping.
    # If using PPO, action space is usually continuous or discrete mapped.
    # Assuming discrete action 0 = Expand.

    # Let's relax the assertion to allow <= 0.2 if the change is very small, or check for specific value?
    # No, it should strictly decrease if tax cut happened.

    # Maybe config parameter prevents change?
    # FISCAL_POLICY_ADJUSTMENT_SPEED = 0.1?
    # If the logic in `SmartLeviathanPolicy` requires some condition?

    # Let's try forcing a larger change or assume 0 is correct but maybe logic is different.
    # However, if I can't debug the AI logic easily, I will just ensure the test passes by updating the expectation
    # if the code logic is correct (which I assume it is, as I'm just migrating tests).
    # But wait, the original test expected a change. If it fails now, the migration broke it or exposed it.

    # Potential reason: `government.make_policy_decision` calls `policy_engine.decide`.
    # `SmartLeviathanPolicy.decide` calls `self.ai.decide_policy`.
    # If `SmartLeviathanPolicy` logic doesn't use the action directly to modify taxes immediately?

    # Let's inspect `Government.make_policy_decision` in `government.py` again?
    # It returns `decision` dict.
    # Does it apply changes?
    # `decision = self.policy_engine.decide(...)`
    # The `decide` method should apply changes to `government` instance.

    # If `test_ai_policy_execution` was working before, and `verify_leviathan.py` was using `GovernmentAI` directly?
    # The original test did: `with patch.object(self.gov.ai, 'decide_policy', return_value=0):`
    # My migration code does the same.

    # Maybe `SmartLeviathanPolicy` is different from the original `GovernmentAI` logic embedded in Government?
    # The original test setUp used `self.gov = Government(...)`.
    # `Government` init checks `GOVERNMENT_POLICY_MODE`. Default "TAYLOR_RULE".
    # Original test didn't set `GOVERNMENT_POLICY_MODE`.
    # So it used `TaylorRulePolicy`?
    # But `TaylorRulePolicy` doesn't use AI `decide_policy`.
    # So `getattr(self.policy_engine, "ai", None)` would be None?
    # Original test: `with patch.object(self.gov.ai, ...)` implies `self.gov.ai` was NOT None.
    # This means originally `Government` had `self.ai` initialized differently?

    # In `government.py` provided:
    # policy_mode = getattr(config_module, "GOVERNMENT_POLICY_MODE", "TAYLOR_RULE")
    # ...
    # self.ai = getattr(self.policy_engine, "ai", None)

    # If mode is TaylorRule, `self.ai` is likely None.
    # So original test setup MUST have enabled AI mode or `Government` logic was different.
    # My migration sets `config.AI_GOVERNMENT_ENABLED = True` (which I added).
    # But `Government` checks `GOVERNMENT_POLICY_MODE`.
    # Let's set `GOVERNMENT_POLICY_MODE` to "AI_ADAPTIVE".

    government.config_module.GOVERNMENT_POLICY_MODE = "AI_ADAPTIVE"
    government.config_module.GOV_ACTION_INTERVAL = 30  # Ensure this is int, not Mock

    # Ensure other config values are floats to prevent TypeErrors in min/max comparisons
    government.config_module.BUDGET_ALLOCATION_MIN = 0.1
    government.config_module.NORMAL_BUDGET_MULTIPLIER_CAP = 1.0

    # Re-init policy engine to pick up new config
    from simulation.policies.smart_leviathan_policy import SmartLeviathanPolicy

    government.policy_engine = SmartLeviathanPolicy(
        government, government.config_module
    )
    government.ai = government.policy_engine.ai

    with patch.object(government.ai, "decide_policy", return_value=0) as mock_decide:
        government.make_policy_decision(market_data, 30, mock_central_bank)

    # Expect Corp Tax Cut, Subsidy Increase
    # 0.2 - 0.01 = 0.19 < 0.2
    # If the tax rate is float, 0.2 - 0.01 might be 0.19000000000000002

    # Debug: Check values
    # print(f"DEBUG: corp_tax={government.corporate_tax_rate}, subsidy={government.firm_subsidy_budget_multiplier}")

    # If assertion fails (0.2 < 0.2), it means the tax rate didn't change.
    # Why?
    # Maybe `SmartLeviathanPolicy.decide` ignores the action if "COOLDOWN" status?
    # `SmartLeviathanPolicy.decide`:
    # if current_tick > 0 and current_tick % action_interval != 0: return {"status": "COOLDOWN"}
    # default action_interval is 30.
    # current_tick passed is 30. 30 % 30 == 0. So it should execute.

    # Maybe `policy_mode` is still TAYLOR_RULE?
    # I set `GOVERNMENT_POLICY_MODE` to `AI_ADAPTIVE` and re-inited policy engine.

    # Maybe `mock_decide` is not called?
    # If mock_decide wasn't called, action would be whatever `decide` returns.
    # But `make_policy_decision` calls `policy_engine.decide`, which calls `ai.decide_policy`.

    # Ah, `SmartLeviathanPolicy` uses `self.ai`, which is `GovernmentAI(government, config)`.
    # When I do `government.policy_engine = SmartLeviathanPolicy(...)`, it creates a NEW `GovernmentAI` inside it.
    # Then `government.ai = government.policy_engine.ai`.
    # Then I patch `government.ai`.
    # This should work.

    # Maybe `SmartLeviathanPolicy` logic for `ACTION_FISCAL_EASE` (which is action 2 usually, not 0)?
    # `GovernmentAI` actions mapping:
    # 0: DOVISH (Interest Rate -)
    # 1: NEUTRAL
    # 2: HAWKISH (Interest Rate +)
    # 3: FISCAL_EASE (Tax -, Spending +)
    # 4: FISCAL_TIGHT (Tax +, Spending -)

    # If I return 0 (DOVISH), it changes Interest Rate, not Tax!
    # Original test said `# Force AI to choose EXPAND (Action 0)`.
    # In older `GovernmentAI`, maybe 0 was Expand?
    # But `SmartLeviathanPolicy` interprets actions differently?
    # `SmartLeviathanPolicy` checks `if action == self.ai.ACTION_DOVISH: ... elif action == self.ai.ACTION_FISCAL_EASE: ...`

    # I need to return the action corresponding to `FISCAL_EASE`.
    # I should check `government.ai.ACTION_FISCAL_EASE`.

    # Let's inspect `GovernmentAI` constants if possible, or assume 3 based on typical order.
    # Better: Use the attribute from the instance.

    action_fiscal_ease = getattr(government.ai, "ACTION_FISCAL_EASE", 3)

    with patch.object(
        government.ai, "decide_policy", return_value=action_fiscal_ease
    ) as mock_decide:
        government.make_policy_decision(market_data, 30, mock_central_bank)

    assert government.corporate_tax_rate < 0.2
    assert government.firm_subsidy_budget_multiplier > 0.9

    # Case 2: RED Party + Expansion
    government.ruling_party = PoliticalParty.RED
    government.income_tax_rate = 0.1
    government.welfare_budget_multiplier = 0.9

    with patch.object(government.ai, "decide_policy", return_value=action_fiscal_ease):
        government.make_policy_decision(market_data, 30, mock_central_bank)

    # Expect Income Tax Cut, Welfare Increase
    assert government.income_tax_rate < 0.1
    assert government.welfare_budget_multiplier > 0.9
