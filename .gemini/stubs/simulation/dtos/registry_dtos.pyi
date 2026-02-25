from pydantic import BaseModel
from typing import Any, Literal

class ParameterSchemaDTO(BaseModel):
    """
    UI 위젯 생성을 위한 메타데이터 정의.
    Matches the schema in config/domains/registry_schema.yaml.
    """
    key: str
    label: str
    description: str
    widget_type: Literal['slider', 'toggle', 'number_input', 'select']
    data_type: Literal['int', 'float', 'bool', 'str']
    min_value: float | int | None
    max_value: float | int | None
    step: float | int | None
    options: list[Any] | None
    category: str
    unit: str | None
