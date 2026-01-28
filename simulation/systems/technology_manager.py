from __future__ import annotations
import logging
import random
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.dtos.strategy import ScenarioStrategy

from simulation.systems.tech.api import FirmTechInfoDTO

logger = logging.getLogger(__name__)

@dataclass
class TechNode:
    id: str
    name: str
    sector: str  # e.g., "FOOD", "MANUFACTURING"
    multiplier: float  # e.g., 3.0 (+200%)
    cost_threshold: float # WO-136: Cost threshold for probabilistic unlock
    diffusion_rate: float  # Probability of adoption per tick for non-visionaries
    is_unlocked: bool = False

class TechnologyManager:
    """
    Phase 23: Technology Manager
    Handles the invention and diffusion of new technologies (The S-Curve).
    """

    def __init__(self, config_module: Any, logger: logging.Logger, strategy: Optional["ScenarioStrategy"] = None):
        self.config = config_module
        self.logger = logger
        self.strategy = strategy
        
        # Tech Registry
        self.tech_tree: Dict[str, TechNode] = {}
        self.active_techs: List[str] = [] # List of unlocked tech IDs
        
        # Adoption Registry: {FirmID: {TechID}}
        self.adoption_registry: Dict[int, Set[str]] = {}
        
        self.human_capital_index: float = 1.0 # WO-054

        self._initialize_tech_tree()

    def _initialize_tech_tree(self):
        """Define the initial tech tree."""
        # WO-053: Chemical Fertilizer
        # WO-136: Use Strategy DTO if available
        tfp_mult = self.strategy.tfp_multiplier if self.strategy else getattr(self.config, "TECH_FERTILIZER_MULTIPLIER", 3.0)
        # WO-136: Replaced unlock_tick with cost_threshold
        # unlock_tick was 50. Approx R&D per tick per firm is ~2-5. 10 firms -> 20-50 per tick. 50 ticks -> 1000-2500.
        # We'll set a safe default of 5000.0
        cost_threshold = 5000.0
        diff_rate = self.strategy.tech_diffusion_rate if self.strategy else getattr(self.config, "TECH_DIFFUSION_RATE", 0.05)

        fertilizer = TechNode(
            id="TECH_AGRI_CHEM_01",
            name="Chemical Fertilizer (Haber-Bosch)",
            sector="FOOD",
            multiplier=tfp_mult,
            cost_threshold=cost_threshold,
            diffusion_rate=diff_rate
        )
        self.tech_tree[fertilizer.id] = fertilizer

    def update(self, current_tick: int, firms: List[FirmTechInfoDTO], human_capital_index: float) -> None:
        """
        Called every tick.
        1. Check Unlocks.
        2. Process Diffusion (Spread).
        """
        # WO-054: Update Human Capital Index from parameter
        self.human_capital_index = human_capital_index

        # WO-136: Aggregate R&D by sector
        current_rd_by_sector: Dict[str, float] = {}
        for firm in firms:
            sector = firm["sector"]
            rd = firm.get("current_rd_investment", 0.0)
            current_rd_by_sector[sector] = current_rd_by_sector.get(sector, 0.0) + rd

        # 1. Unlock Check (Probabilistic)
        self._check_probabilistic_unlocks(current_rd_by_sector, firms, current_tick)

        # 2. Diffusion Process (S-Curve)
        self._process_diffusion(firms, current_tick)

    def _check_probabilistic_unlocks(self, current_rd_by_sector: Dict[str, float], firms: List[FirmTechInfoDTO], current_tick: int):
        """
        WO-136: Probabilistic unlock based on accumulated R&D.
        P = min(0.1, (Sector_Accumulated_RD / Tech_Cost_Threshold)^2)
        """
        for tech in self.tech_tree.values():
            if tech.is_unlocked:
                continue

            sector_rd = current_rd_by_sector.get(tech.sector, 0.0)
            if tech.sector == "ALL":
                # Sum all sectors if tech is universal
                sector_rd = sum(current_rd_by_sector.values())

            if sector_rd <= 0:
                continue

            # Calculate probability
            ratio = sector_rd / tech.cost_threshold
            prob = min(0.1, ratio ** 2)

            # Roll dice
            if random.random() < prob:
                self._unlock_tech(tech, firms, current_tick)

    def _unlock_tech(self, tech: TechNode, firms: List[FirmTechInfoDTO], current_tick: int):
        """Unlock technology and assign to Early Adopters (Visionaries)."""
        tech.is_unlocked = True
        self.active_techs.append(tech.id)
        
        # Immediate Adoption by Visionaries
        early_adopters_count = 0
        for firm_dto in firms:
            # Check sector match even for visionaries
            if firm_dto["sector"] != tech.sector and tech.sector != "ALL":
                continue

            # Visionary Firms
            if firm_dto["is_visionary"]:
                self._adopt(firm_dto["id"], tech)
                early_adopters_count += 1
        
        self.logger.info(
            f"TECH_UNLOCK | Unlocked {tech.name} (ID: {tech.id}). "
            f"Early Adopters: {early_adopters_count} firms.",
            extra={"tick": current_tick, "tech_id": tech.id}
        )

    def _get_effective_diffusion_rate(self, base_rate: float) -> float:
        """
        WO-054: Tech Diffusion Feedback Loop
        current_rate = base_rate * (1 + min(1.5, 0.5 * (avg_edu_level - 1.0)))
        """
        # avg_edu_level is self.human_capital_index
        # Formula: 1.0 + min(1.5, 0.5 * (HCI - 1.0))
        # Example: HCI=4.0 -> 0.5 * 3.0 = 1.5 -> Boost = 1.5 -> Rate = Base * 2.5
        # Example: HCI=1.0 -> 0.0 -> Boost = 0.0 -> Rate = Base * 1.0

        boost = min(1.5, 0.5 * max(0.0, self.human_capital_index - 1.0))
        return base_rate * (1.0 + boost)

    def _process_diffusion(self, firms: List[FirmTechInfoDTO], current_tick: int):
        """
        Simulate the spread of technology to non-adopters.
        WO-136: Vectorized implementation for 2,000+ agents.
        """
        if not firms:
            return

        # Pre-process firms into arrays for vectorized operations
        # Note: In a real persistent vector engine, these would be maintained as state.
        # Here we convert on the fly, which is still faster for large N than looping python objects.
        firm_ids = np.array([f["id"] for f in firms])
        sectors = np.array([f["sector"] for f in firms])

        # We need a way to check adoption efficiently.
        # Construct a boolean mask of who has adopted what.
        # But adoption_registry is Dict[int, Set[str]].
        # For each tech, we can build a mask of "already_adopted".

        for tech_id in self.active_techs:
            tech = self.tech_tree[tech_id]
            
            # WO-054: Calculate effective rate
            effective_rate = self._get_effective_diffusion_rate(tech.diffusion_rate)

            # 1. Sector Mask
            if tech.sector == "ALL":
                sector_mask = np.ones(len(firms), dtype=bool)
            else:
                sector_mask = (sectors == tech.sector)

            if not np.any(sector_mask):
                continue

            # 2. Adoption Mask (True if already adopted)
            # This part involves dictionary lookups, can be optimized if adoption_registry was a matrix.
            # For now, we use a list comprehension which is fast enough for <10k agents.
            already_adopted_mask = np.array([
                self.has_adopted(fid, tech_id) for fid in firm_ids
            ], dtype=bool)

            # 3. Candidates: In Sector AND Not Adopted
            candidate_mask = sector_mask & (~already_adopted_mask)

            candidate_indices = np.where(candidate_mask)[0]
            if len(candidate_indices) == 0:
                continue

            # 4. Roll Dice (Vectorized)
            # Create random numbers for all candidates
            random_rolls = np.random.rand(len(candidate_indices))

            # 5. Determine Adopters
            adopter_indices = candidate_indices[random_rolls < effective_rate]

            # 6. Apply Adoption
            for idx in adopter_indices:
                firm_id = int(firm_ids[idx]) # Convert numpy int to python int
                self._adopt(firm_id, tech)
                self.logger.info(
                    f"TECH_DIFFUSION | Firm {firm_id} adopted {tech.name}. Rate: {effective_rate:.4f} (Base: {tech.diffusion_rate})",
                    extra={"tick": current_tick, "agent_id": firm_id, "tech_id": tech.id}
                )

    def _adopt(self, firm_id: int, tech: TechNode):
        """Register adoption."""
        if firm_id not in self.adoption_registry:
            self.adoption_registry[firm_id] = set()
        self.adoption_registry[firm_id].add(tech.id)

    def has_adopted(self, firm_id: int, tech_id: str) -> bool:
        if firm_id not in self.adoption_registry:
            return False
        return tech_id in self.adoption_registry[firm_id]

    def get_productivity_multiplier(self, firm_id: int) -> float:
        """
        Calculate total TFP multiplier for a firm based on adopted techs.
        """
        if firm_id not in self.adoption_registry:
            return 1.0
        
        total_mult = 1.0
        adopted_techs = self.adoption_registry[firm_id]
        
        for tech_id in adopted_techs:
            tech = self.tech_tree.get(tech_id)
            if tech:
                # Multiplicative or Additive?
                # Spec says "Multiplies productivity_factor by 3.0".
                # If multiple techs? Usually multiplicative for TFP.
                total_mult *= tech.multiplier
        
        return total_mult
