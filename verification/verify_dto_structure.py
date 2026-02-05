import json
import dataclasses
from dataclasses import asdict
from simulation.dtos.watchtower import (
    WatchtowerSnapshotDTO, IntegrityDTO, MacroDTO, FinanceDTO,
    FinanceRatesDTO, FinanceSupplyDTO, PoliticsDTO, PoliticsApprovalDTO,
    PoliticsStatusDTO, PoliticsFiscalDTO, PopulationDTO,
    PopulationDistributionDTO, PopulationMetricsDTO
)

MOCK_PATH = "design/3_work_artifacts/specs/golden_samples/watchtower_full_mock_v2.json"

def verify_dto():
    print(f"Loading mock from {MOCK_PATH}...")
    with open(MOCK_PATH, 'r') as f:
        mock_data = json.load(f)

    print("Instantiating DTOs...")
    try:
        # Manual instantiation to check every field matches
        snapshot = WatchtowerSnapshotDTO(
            tick=mock_data['tick'],
            status=mock_data['status'],
            integrity=IntegrityDTO(**mock_data['integrity']),
            macro=MacroDTO(**mock_data['macro']),
            finance=FinanceDTO(
                rates=FinanceRatesDTO(**mock_data['finance']['rates']),
                supply=FinanceSupplyDTO(**mock_data['finance']['supply'])
            ),
            politics=PoliticsDTO(
                approval=PoliticsApprovalDTO(**mock_data['politics']['approval']),
                status=PoliticsStatusDTO(**mock_data['politics']['status']),
                fiscal=PoliticsFiscalDTO(**mock_data['politics']['fiscal'])
            ),
            population=PopulationDTO(
                distribution=PopulationDistributionDTO(**mock_data['population']['distribution']),
                active_count=mock_data['population']['active_count'],
                metrics=PopulationMetricsDTO(**mock_data['population']['metrics'])
            )
        )
        print("DTO instantiated successfully.")
    except TypeError as e:
        print(f"FAILED to instantiate DTO: {e}")
        exit(1)
    except KeyError as e:
        print(f"FAILED to find key in mock: {e}")
        exit(1)

    print("Converting back to dict...")
    dto_dict = asdict(snapshot)

    print("Comparing structures...")
    # Basic check - keys should match
    # Note: floating point comparison might be tricky for exact equality,
    # but structure equality is what we care about here.

    # Check top level keys
    assert dto_dict.keys() == mock_data.keys()

    # Check nested keys recursively (simplified)
    assert dto_dict['integrity'] == mock_data['integrity']
    assert dto_dict['macro'] == mock_data['macro']
    assert dto_dict['finance'] == mock_data['finance']
    assert dto_dict['politics'] == mock_data['politics']
    # Population metrics might need float tolerance if logic was involved, but here it's pass-through
    assert dto_dict['population'] == mock_data['population']

    print("VERIFICATION PASSED: DTO matches Mock exactly.")

if __name__ == "__main__":
    verify_dto()
