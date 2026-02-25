import logging
from _typeshed import Incomplete
from dataclasses import dataclass, field as field
from simulation.dtos.strategy import ScenarioStrategy as ScenarioStrategy
from simulation.systems.tech.api import FirmTechInfoDTO as FirmTechInfoDTO
from typing import Any

logger: Incomplete

@dataclass
class TechNode:
    id: str
    name: str
    sector: str
    multiplier: float
    cost_threshold: float
    diffusion_rate: float
    is_unlocked: bool = ...

class TechnologyManager:
    """
    Phase 23: Technology Manager
    Handles the invention and diffusion of new technologies (The S-Curve).
    """
    config: Incomplete
    logger: Incomplete
    strategy: Incomplete
    tech_tree: dict[str, TechNode]
    active_techs: list[str]
    adoption_matrix: Incomplete
    tech_id_to_idx: dict[str, int]
    idx_to_tech_id: list[str]
    human_capital_index: float
    def __init__(self, config_module: Any, logger: logging.Logger, strategy: ScenarioStrategy | None = None) -> None: ...
    def update(self, current_tick: int, firms: list[FirmTechInfoDTO], human_capital_index: float) -> None:
        """
        Called every tick.
        1. Check Unlocks.
        2. Process Diffusion (Spread).
        """
    def has_adopted(self, firm_id: int, tech_id: str) -> bool: ...
    def get_productivity_multiplier(self, firm_id: int) -> float:
        """
        Calculate total TFP multiplier for a firm based on adopted techs.
        """
