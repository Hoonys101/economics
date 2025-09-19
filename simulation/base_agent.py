from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

class BaseAgent(ABC):
    def __init__(self, id: int, initial_assets: float, initial_needs: Dict[str, float], decision_engine, value_orientation: str, name: str = None, logger=None):
        self.id = id
        self.assets = initial_assets
        self.needs = initial_needs
        self.decision_engine = decision_engine
        self.value_orientation = value_orientation
        self.name = name if name is not None else f"{self.__class__.__name__}_{id}"
        self.inventory: Dict[str, float] = {}
        self.is_active: bool = True
        self.logger = logger if logger is not None else logging.getLogger(self.name)

    @abstractmethod
    def update_needs(self, current_tick: int):
        pass

    @abstractmethod
    def make_decision(self, current_tick: int, market_data: Dict[str, Any]):
        pass
