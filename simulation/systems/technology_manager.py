from __future__ import annotations
import logging
import random
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger(__name__)

@dataclass
class TechNode:
    id: str
    name: str
    sector: str  # e.g., "FOOD", "MANUFACTURING"
    multiplier: float  # e.g., 3.0 (+200%)
    unlock_tick: int
    diffusion_rate: float  # Probability of adoption per tick for non-visionaries
    is_unlocked: bool = False

class TechnologyManager:
    """
    Phase 23: Technology Manager
    Handles the invention and diffusion of new technologies (The S-Curve).
    """

    def __init__(self, config_module: Any, logger: logging.Logger):
        self.config = config_module
        self.logger = logger
        
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
        fertilizer = TechNode(
            id="TECH_AGRI_CHEM_01",
            name="Chemical Fertilizer (Haber-Bosch)",
            sector="FOOD",
            multiplier=3.0, # 300% TFP
            unlock_tick=getattr(self.config, "TECH_FERTILIZER_UNLOCK_TICK", 50), # Early unlock for test
            diffusion_rate=getattr(self.config, "TECH_DIFFUSION_RATE", 0.05)
        )
        self.tech_tree[fertilizer.id] = fertilizer

    def update(self, current_tick: int, simulation: Any) -> None:
        """
        Called every tick.
        1. Check Unlocks.
        2. Process Diffusion (Spread).
        """
        # WO-054: Update Human Capital Index based on average education
        self._update_human_capital_index(simulation.households)

        # 1. Unlock Check
        for tech in self.tech_tree.values():
            if not tech.is_unlocked and current_tick >= tech.unlock_tick:
                self._unlock_tech(tech, simulation)

        # 2. Diffusion Process (S-Curve)
        self._process_diffusion(simulation)

    def _update_human_capital_index(self, households: List[Any]):
        """WO-054: Calculate average education level."""
        total_edu = 0
        count = 0
        for h in households:
            if h.is_active:
                total_edu += getattr(h, "education_level", 0)
                count += 1

        if count > 0:
            self.human_capital_index = total_edu / count
        else:
            self.human_capital_index = 1.0 # Default baseline

    def _unlock_tech(self, tech: TechNode, simulation: Any):
        """Unlock technology and assign to Early Adopters (Visionaries)."""
        tech.is_unlocked = True
        self.active_techs.append(tech.id)
        
        # Immediate Adoption by Visionaries
        early_adopters_count = 0
        for firm in simulation.firms:
            if not firm.is_active: continue
            
            # Visionary Firms or Top 10% Wealth (if needed)
            # Using is_visionary attribute if available, else random top slice?
            # Firm has is_visionary since Phase 14-2.
            if getattr(firm, "is_visionary", False):
                self._adopt(firm, tech)
                early_adopters_count += 1
        
        self.logger.info(
            f"TECH_UNLOCK | Unlocked {tech.name} (ID: {tech.id}). "
            f"Early Adopters: {early_adopters_count} firms.",
            extra={"tick": simulation.time, "tech_id": tech.id}
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

    def _process_diffusion(self, simulation: Any):
        """
        Simulate the spread of technology to non-adopters.
        """
        for tech_id in self.active_techs:
            tech = self.tech_tree[tech_id]
            
            # WO-054: Calculate effective rate
            effective_rate = self._get_effective_diffusion_rate(tech.diffusion_rate)

            # Potential Adopters: Firms in relevant sector who haven't adopted yet
            for firm in simulation.firms:
                if not firm.is_active: continue
                # Sector match check (if tech is sector-specific)
                # If tech.sector is "ALL", everyone can adopt.
                # If "FOOD", only firms with specialization in FOOD sector.
                # Firm has 'specialization' (item_id) and 'sector' (e.g. FOOD).
                
                # Check sector compatibility
                # config.GOODS[firm.specialization]['sector'] == tech.sector
                if firm.sector != tech.sector and tech.sector != "ALL":
                    continue

                # Check if already adopted
                if self.has_adopted(firm.id, tech_id):
                    continue
                
                # Diffusion Chance
                if random.random() < effective_rate:
                    self._adopt(firm, tech)
                    self.logger.info(
                        f"TECH_DIFFUSION | Firm {firm.id} adopted {tech.name}. Rate: {effective_rate:.4f} (Base: {tech.diffusion_rate})",
                        extra={"tick": simulation.time, "agent_id": firm.id, "tech_id": tech.id}
                    )

    def _adopt(self, firm: Any, tech: TechNode):
        """Register adoption."""
        if firm.id not in self.adoption_registry:
            self.adoption_registry[firm.id] = set()
        self.adoption_registry[firm.id].add(tech.id)

    def has_adopted(self, firm_id: int, tech_id: str) -> bool:
        if firm_id not in self.adoption_registry:
            return False
        return tech_id in self.adoption_registry[firm_id]

    def get_productivity_multiplier(self, firm_id: int, firm_sector: str) -> float:
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
