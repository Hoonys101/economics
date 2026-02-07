from dataclasses import dataclass
from typing import Dict, Any, Optional, Union, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from modules.memory.api import MemoryV2Interface

@dataclass
class BaseAgentInitDTO:
    """
    Data Transfer Object for BaseAgent initialization.
    Encapsulates all constructor arguments to simplify signature and enforce typing.
    """
    id: int
    initial_assets: Union[float, Dict[str, float]]
    initial_needs: Dict[str, float]
    decision_engine: Any
    value_orientation: str
    name: Optional[str] = None
    logger: Optional[logging.Logger] = None
    memory_interface: Optional["MemoryV2Interface"] = None
