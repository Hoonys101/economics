from typing import TypeVar

T = TypeVar('T')

def create_config_dto(config_module: object, dto_class: type[T]) -> T:
    """
    Dynamically creates and populates a config DTO from a config module.
    It iterates over the DTO's fields and gets the corresponding (uppercase)
    attribute from the config module.
    """
