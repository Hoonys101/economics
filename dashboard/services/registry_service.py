from typing import List, Optional
from dataclasses import dataclass

@dataclass
class RegistryMetadata:
    key: str
    domain: str
    min_value: float
    max_value: float
    step: float
    description: str
    data_type: str = "float" # float, int, bool

class RegistryService:
    """
    Service to provide metadata for simulation parameters.
    Currently uses a hardcoded shim until GlobalRegistry is fully integrated.
    """

    _SHIM_METADATA = [
        RegistryMetadata(
            key="corporate_tax_rate",
            domain="Government",
            min_value=0.0,
            max_value=1.0,
            step=0.01,
            description="Corporate Tax Rate",
            data_type="float"
        ),
         RegistryMetadata(
            key="base_rate",
            domain="Finance",
            min_value=0.0,
            max_value=0.20,
            step=0.0025,
            description="Central Bank Base Interest Rate",
            data_type="float"
        ),
        RegistryMetadata(
            key="welfare_budget",
            domain="Government",
            min_value=0,
            max_value=10000000,
            step=10000,
            description="Total Welfare Budget (Pennies)",
            data_type="int"
        )
    ]

    def get_all_metadata(self) -> List[RegistryMetadata]:
        return self._SHIM_METADATA

    def get_metadata(self, key: str) -> Optional[RegistryMetadata]:
        for meta in self._SHIM_METADATA:
            if meta.key == key:
                return meta
        return None
