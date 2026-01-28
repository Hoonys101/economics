import dataclasses
from typing import Type, TypeVar

T = TypeVar('T')

def create_config_dto(config_module: object, dto_class: Type[T]) -> T:
    """
    Dynamically creates and populates a config DTO from a config module.
    It iterates over the DTO's fields and gets the corresponding (uppercase)
    attribute from the config module.
    """
    dto_fields = {f.name for f in dataclasses.fields(dto_class)}
    config_values = {}

    for field_name in dto_fields:
        config_key = field_name.upper()
        if hasattr(config_module, config_key):
            config_values[field_name] = getattr(config_module, config_key)
        else:
            # This provides a clear error when a config is missing
            raise AttributeError(
                f"Configuration Error: Attribute '{config_key}' not found in config_module "
                f"but is required by DTO '{dto_class.__name__}'."
            )

    return dto_class(**config_values)
