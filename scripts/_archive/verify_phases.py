import sys
import os

# Add repo root to path
sys.path.append(os.getcwd())

from simulation.orchestration.tick_orchestrator import TickOrchestrator
from unittest.mock import MagicMock

def main():
    print("Verifying TickOrchestrator Phases...")

    mock_world_state = MagicMock()
    # Mock specific attributes needed by phases during initialization
    mock_world_state.config_module = MagicMock()

    mock_action_processor = MagicMock()

    try:
        orchestrator = TickOrchestrator(mock_world_state, mock_action_processor)

        expected_order = [
            "Phase0_PreSequence",
            "Phase_Production",
            "Phase1_Decision",
            "Phase_Bankruptcy",
            "Phase_SystemicLiquidation",
            "Phase2_Matching",
            "Phase3_Transaction",
            "Phase_Consumption",
            "Phase5_PostSequence"
        ]

        actual_order = [phase.__class__.__name__ for phase in orchestrator.phases]

        print("\nExpected Order:")
        for p in expected_order:
            print(f" - {p}")

        print("\nActual Order:")
        for p in actual_order:
            print(f" - {p}")

        if actual_order == expected_order:
            print("\nSUCCESS: Phase order matches specification.")
        else:
            print("\nFAILURE: Phase order mismatch!")
            sys.exit(1)

    except Exception as e:
        print(f"\nERROR during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
