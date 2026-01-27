
import logging
from simulation.dtos import DecisionContext, HouseholdConfigDTO
from simulation.decisions.base_decision_engine import BaseDecisionEngine
try:
    from modules.household.dtos import HouseholdStateDTO
except ImportError:
    # Minimal mock if module not found in path setup (but should be fine in script)
    from dataclasses import dataclass
    @dataclass
    class HouseholdStateDTO:
        pass

def test_strictness():
    print("Testing DecisionContext strictness...")
    try:
        # Attempt to inject 'household' which should be removed
        ctx = DecisionContext(
            state=None,
            config=None,
            markets={},
            goods_data=[],
            market_data={},
            current_time=0,
            household="I am an impostor"
        )
        print("FAIL: DecisionContext accepted 'household' argument.")
    except TypeError as e:
        print(f"PASS: DecisionContext raised TypeError as expected: {e}")
    except Exception as e:
        print(f"FAIL: Unexpected exception: {type(e)} {e}")

def test_purity_gate_assertions():
    print("Testing Purity Gate assertions...")
    
    class TestEngine(BaseDecisionEngine):
        def _make_decisions_internal(self, context, macro_context):
            return [], None

    engine = TestEngine()
    
    # 1. Missing State
    try:
        ctx = DecisionContext(
            state=None,
            config=None,
            markets={},
            goods_data=[],
            market_data={},
            current_time=0
        )
        engine.make_decisions(ctx)
        print("FAIL: Purity Gate did not catch missing state.")
    except AssertionError as e:
        print(f"PASS: Caught missing state: {e}")

    # 2. Missing Config
    try:
        # Mock state so first assert passes
        ctx = DecisionContext(
            state="ValidState",
            config=None,
            markets={},
            goods_data=[],
            market_data={},
            current_time=0
        )
        engine.make_decisions(ctx)
        print("FAIL: Purity Gate did not catch missing config.")
    except AssertionError as e:
        print(f"PASS: Caught missing config: {e}")

if __name__ == "__main__":
    test_strictness()
    test_purity_gate_assertions()
