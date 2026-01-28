import pytest
from dataclasses import dataclass
from types import SimpleNamespace
from simulation.utils.config_factory import create_config_dto

@dataclass
class SampleConfigDTO:
    field_a: int
    field_b: str
    field_c: float

def test_create_config_dto_success():
    mock_config = SimpleNamespace(
        FIELD_A=10,
        FIELD_B="test",
        FIELD_C=3.14,
        OTHER_FIELD="ignored"
    )

    dto = create_config_dto(mock_config, SampleConfigDTO)

    assert dto.field_a == 10
    assert dto.field_b == "test"
    assert dto.field_c == 3.14

def test_create_config_dto_missing_field():
    mock_config = SimpleNamespace(
        FIELD_A=10,
        # FIELD_B is missing
        FIELD_C=3.14
    )

    with pytest.raises(AttributeError) as excinfo:
        create_config_dto(mock_config, SampleConfigDTO)

    assert "FIELD_B" in str(excinfo.value)
    assert "SampleConfigDTO" in str(excinfo.value)
