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

    # Internal index for vectorization
    _idx: int = -1

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
        
        # Vectorized Adoption Registry (WO-136)
        # Rows: Firm ID (mapped directly if small, or via map if sparse/large)
        # We assume Firm IDs are effectively < 50000.
        # adoption_matrix[firm_id, tech_idx] = True/False
        self.adoption_matrix = np.zeros((1000, 0), dtype=bool)

        self.tech_id_to_idx: Dict[str, int] = {}
        self.idx_to_tech_id: List[str] = []
        
        self.human_capital_index: float = 1.0 # WO-054

        self._initialize_tech_tree()

    def _initialize_tech_tree(self):
        """Define the initial tech tree."""
        # WO-053: Chemical Fertilizer
        # WO-136: Use Strategy DTO if available
        tfp_mult = self.strategy.tfp_multiplier if self.strategy else getattr(self.config, "TECH_FERTILIZER_MULTIPLIER", 3.0)
        # WO-136: Replaced unlock_tick with cost_threshold
        # cost_threshold is now configurable via TECH_UNLOCK_COST_THRESHOLD
        cost_threshold = getattr(self.config, "TECH_UNLOCK_COST_THRESHOLD", 5000.0)
        diff_rate = self.strategy.tech_diffusion_rate if self.strategy else getattr(self.config, "TECH_DIFFUSION_RATE", 0.05)

        fertilizer = TechNode(
            id="TECH_AGRI_CHEM_01",
            name="Chemical Fertilizer (Haber-Bosch)",
            sector="FOOD_PROD",
            multiplier=tfp_mult,
            cost_threshold=cost_threshold,
            diffusion_rate=diff_rate
        )
        self._register_tech(fertilizer)

    def _register_tech(self, tech: TechNode):
        """Register a tech node and assign it an index."""
        if tech.id in self.tech_tree:
            return

        tech._idx = len(self.idx_to_tech_id)
        self.tech_id_to_idx[tech.id] = tech._idx
        self.idx_to_tech_id.append(tech.id)
        self.tech_tree[tech.id] = tech

        # Resize adoption matrix to include new tech column
        current_rows = self.adoption_matrix.shape[0]
        # Create new column of zeros
        new_col = np.zeros((current_rows, 1), dtype=bool)
        self.adoption_matrix = np.hstack((self.adoption_matrix, new_col))

    def _ensure_capacity(self, max_firm_id: int):
        """Resize adoption matrix rows if necessary."""
        current_rows = int(self.adoption_matrix.shape[0])
        # TD-TEST-MOCK-LEAK: Prevent comparison between MagicMock and int
        try:
            if not isinstance(max_firm_id, int):
                max_firm_id = int(max_firm_id)
        except (TypeError, ValueError):
            return

        if max_firm_id >= current_rows:
            # Expand to at least double or max_id + buffer
            new_rows = max(max_firm_id + 1, current_rows * 2)
            rows_to_add = new_rows - current_rows
            cols = int(self.adoption_matrix.shape[1])

            # Append zeros
            padding = np.zeros((rows_to_add, cols), dtype=bool)
            self.adoption_matrix = np.vstack((self.adoption_matrix, padding))

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
        self._check_probabilistic_unlocks(current_rd_by_sector, current_tick)

        # 2. Diffusion Process (S-Curve)
        self._process_diffusion(firms, current_tick)

    def _check_probabilistic_unlocks(self, current_rd_by_sector: Dict[str, float], current_tick: int):
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
            # WO-136: Probability cap is configurable
            prob_cap = getattr(self.config, "TECH_UNLOCK_PROB_CAP", 0.1)
            prob = min(prob_cap, ratio ** 2)

            # Roll dice
            if random.random() < prob:
                self._unlock_tech(tech, current_tick)

    def _unlock_tech(self, tech: TechNode, current_tick: int):
        """Unlock technology."""
        tech.is_unlocked = True
        self.active_techs.append(tech.id)
        
        self.logger.info(
            f"TECH_UNLOCK | Unlocked {tech.name} (ID: {tech.id}).",
            extra={"tick": current_tick, "tech_id": tech.id}
        )

    def _get_effective_diffusion_rate(self, base_rate: float) -> float:
        """
        WO-054: Tech Diffusion Feedback Loop
        current_rate = base_rate * (1 + min(1.5, 0.5 * (avg_edu_level - 1.0)))
        """
        boost = min(1.5, 0.5 * max(0.0, self.human_capital_index - 1.0))
        return base_rate * (1.0 + boost)

    def _process_diffusion(self, firms: List[FirmTechInfoDTO], current_tick: int):
        """
        Simulate the spread of technology to non-adopters.
        WO-136: Vectorized implementation for 2,000+ agents using Numpy Matrix.
        """
        if not firms:
            return

        firm_ids = np.array([f["id"] for f in firms], dtype=int)

        # Ensure matrix capacity
        max_firm_id = np.max(firm_ids)
        self._ensure_capacity(max_firm_id)

        sectors = np.array([f["sector"] for f in firms])

        for tech_id in self.active_techs:
            tech = self.tech_tree[tech_id]
            tech_idx = tech._idx
            
            # WO-054: Calculate effective rate
            effective_rate = self._get_effective_diffusion_rate(tech.diffusion_rate)

            # 1. Sector Mask
            if tech.sector == "ALL":
                sector_mask = np.ones(len(firms), dtype=bool)
            else:
                sector_mask = (sectors == tech.sector)

            if not np.any(sector_mask):
                continue

            # 2. Adoption Mask (Fast Vectorized Lookup)
            # adoption_matrix[firm_ids, tech_idx] returns array of booleans corresponding to firms
            already_adopted_mask = self.adoption_matrix[firm_ids, tech_idx]

            # 3. Candidates: In Sector AND Not Adopted
            candidate_mask = sector_mask & (~already_adopted_mask)

            candidate_indices = np.where(candidate_mask)[0]
            if len(candidate_indices) == 0:
                continue

            # 4. Roll Dice (Vectorized)
            random_rolls = np.random.rand(len(candidate_indices))

            # 5. Determine Adopters
            adopter_indices = candidate_indices[random_rolls < effective_rate]

            if len(adopter_indices) == 0:
                continue

            # 6. Apply Adoption
            adopter_firm_ids = firm_ids[adopter_indices]

            # Batch update adoption matrix
            self.adoption_matrix[adopter_firm_ids, tech_idx] = True

            # Logging (this loop is now the only O(NewAdopters) part)
            for firm_id in adopter_firm_ids:
                 self.logger.info(
                    f"TECH_DIFFUSION | Firm {firm_id} adopted {tech.name}. Rate: {effective_rate:.4f} (Base: {tech.diffusion_rate})",
                    extra={"tick": current_tick, "agent_id": int(firm_id), "tech_id": tech.id}
                )

    def _adopt(self, firm_id: int, tech: TechNode):
        """Register adoption (Legacy/Manual)."""
        self._ensure_capacity(firm_id)
        self.adoption_matrix[firm_id, tech._idx] = True

    def has_adopted(self, firm_id: int, tech_id: str) -> bool:
        tech_idx = self.tech_id_to_idx.get(tech_id)
        if tech_idx is None:
            return False

        if hasattr(self.adoption_matrix, 'shape') and not hasattr(self.adoption_matrix.shape[0], '_mock_name') and firm_id >= self.adoption_matrix.shape[0]:
            return False

        return bool(self.adoption_matrix[firm_id, tech_idx])

    def get_productivity_multiplier(self, firm_id: int) -> float:
        """
        Calculate total TFP multiplier for a firm based on adopted techs.
        """
        if firm_id >= int(self.adoption_matrix.shape[0]):
            return 1.0
        
        # Get all adopted techs for this firm
        # row: self.adoption_matrix[firm_id] -> boolean array
        adopted_indices = np.where(self.adoption_matrix[firm_id])[0]
        
        total_mult = 1.0
        for tech_idx in adopted_indices:
            tech_id = self.idx_to_tech_id[tech_idx]
            tech = self.tech_tree[tech_id]
            total_mult *= tech.multiplier
        
        return total_mult
