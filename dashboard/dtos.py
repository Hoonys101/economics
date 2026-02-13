from typing import TypedDict, Any, List, Optional, Union, Literal

class ParameterSchemaDTO(TypedDict):
    """
    UI 위젯 생성을 위한 메타데이터 정의.
    Matches the schema in config/domains/registry_schema.yaml.
    """
    key: str
    label: str
    description: str
    widget_type: Literal["slider", "toggle", "number_input", "select"]
    data_type: Literal["int", "float", "bool", "str"]
    min_value: Optional[Union[float, int]]
    max_value: Optional[Union[float, int]]
    step: Optional[Union[float, int]]
    options: Optional[List[Any]]
    category: str
    unit: Optional[str]
