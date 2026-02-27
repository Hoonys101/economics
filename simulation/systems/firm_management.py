from __future__ import annotations
import logging
import random
from typing import TYPE_CHECKING, Optional, Dict, Any

from modules.simulation.dtos.api import FirmConfigDTO
from simulation.utils.config_factory import create_config_dto
from modules.system.api import DEFAULT_CURRENCY
from modules.simulation.api import IAgent

if TYPE_CHECKING:
    from simulation.engine import Simulation
    from simulation.core_agents import Household
    from simulation.firms import Firm

logger = logging.getLogger(__name__)

class FirmSystem:
    """
    Phase 22.5: Firm Management System
    Handles firm creation (entrepreneurship) and lifecycle management.
    """

    def __init__(self, config_module: Any, strategy: Optional["ScenarioStrategy"] = None):
        self.config = config_module
        self.strategy = strategy

    def spawn_firm(self, simulation: "Simulation", founder_household: "Household") -> Optional["Firm"]:
        """
        Wealthy households found new firms.
        """
        base_startup_cost = getattr(self.config, "STARTUP_COST", 30000.0)

        # 1. Choose Specialization First to calculate REAL cost
        specializations = list(self.config.GOODS.keys())
        specialization = random.choice(specializations)
            
        goods_config = self.config.GOODS.get(specialization, {})
        sector = goods_config.get("sector", "OTHER")

        final_startup_cost = base_startup_cost
        has_inputs = bool(goods_config.get("inputs"))
        if has_inputs:
             final_startup_cost *= 1.5

        # 2. Capital Deduction Check
        assets = founder_household.assets
        if isinstance(assets, dict):
            current_assets = assets.get(DEFAULT_CURRENCY, 0.0)
        else:
            try:
                current_assets = float(assets)
            except (TypeError, ValueError):
                current_assets = 0.0

        if current_assets < final_startup_cost:
            return None

        # 3. Generate New Firm ID
        # Filter for integer IDs only (CentralBank might have string ID)
        max_id = max([a.id for a in simulation.agents.values() if isinstance(a.id, int)], default=0)
        new_firm_id = max_id + 1

        # 4. AI Setup
        from simulation.ai.firm_ai import FirmAI
        from simulation.ai.service_firm_ai import ServiceFirmAI
        from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
        from simulation.decisions.rule_based_firm_engine import RuleBasedFirmDecisionEngine
        from simulation.firms import Firm
        from simulation.service_firms import ServiceFirm

        value_orientation = random.choice([
            self.config.VALUE_ORIENTATION_WEALTH_AND_NEEDS,
            self.config.VALUE_ORIENTATION_NEEDS_AND_GROWTH,
        ])
        ai_decision_engine = simulation.ai_trainer.get_engine(value_orientation)

        is_service = specialization in getattr(self.config, "SERVICE_SECTORS", [])

        if is_service:
            firm_ai = ServiceFirmAI(agent_id=str(new_firm_id), ai_decision_engine=ai_decision_engine)
        else:
            firm_ai = FirmAI(agent_id=str(new_firm_id), ai_decision_engine=ai_decision_engine)

        # WO-136: Determine Decision Engine using Strategy or Config
        engine_type = None
        if self.strategy:
             if self.strategy.firm_decision_engine:
                 engine_type = self.strategy.firm_decision_engine
             elif self.strategy.firm_decision_mode == "SEQUENTIAL":
                 engine_type = "RULE_BASED"

        # Fallback to config if not set by strategy
        if engine_type is None:
             engine_type = getattr(self.config, "FIRM_DECISION_ENGINE", "AI_DRIVEN")

        # Normalize and compare
        if str(engine_type).upper() in ["RULE_BASED", "SEQUENTIAL"]:
             firm_decision_engine = RuleBasedFirmDecisionEngine(config_module=self.config, logger=simulation.logger)
        else:
             firm_decision_engine = AIDrivenFirmDecisionEngine(firm_ai, self.config, simulation.logger)

        # 5. Create Firm via Factory (Atomic Registration -> Account -> Transfer)
        from modules.firm.services.firm_factory import FirmFactory
        
        # Create Config DTO
        firm_config_dto = create_config_dto(self.config, FirmConfigDTO)

        # Create Core Config
        from modules.simulation.api import AgentCoreConfigDTO
        initial_needs = {"liquidity_need": getattr(self.config, "INITIAL_FIRM_LIQUIDITY_NEED_MEAN", 50.0)}

        core_config = AgentCoreConfigDTO(
            id=new_firm_id,
            name=f"Firm_{new_firm_id}",
            value_orientation=value_orientation,
            initial_needs=initial_needs,
            logger=simulation.logger,
            memory_interface=None
        )

        loan_market = simulation.markets.get("loan_market")

        # Atomic Creation & Injection
        new_firm = FirmFactory.create_and_register_firm(
            simulation=simulation,
            instance_class=ServiceFirm if is_service else Firm,
            core_config=core_config,
            firm_config_dto=firm_config_dto,
            engine=firm_decision_engine,
            specialization=specialization,
            productivity_factor=random.uniform(8.0, 12.0),
            loan_market=loan_market,
            sector=sector,
            founder=founder_household,
            startup_cost=final_startup_cost
        )

        if not new_firm:
            # FirmFactory handles logging and rollbacks
            return None

        new_firm.founder_id = founder_household.id

        logger.info(
            f"STARTUP | Household {founder_household.id} founded Firm {new_firm_id} "
            f"(Specialization: {specialization}, Capital: {final_startup_cost})"
        )
        return new_firm

    def check_entrepreneurship(self, simulation: "Simulation"):
        """
        Checks entrepreneurship conditions and spawns new firms.
        """
        min_firms = getattr(self.config, "MIN_FIRMS_THRESHOLD", 5)
        startup_cost = getattr(self.config, "STARTUP_COST", 15000.0)
        spirit = getattr(self.config, "ENTREPRENEURSHIP_SPIRIT", 0.05)
        capital_multiplier = getattr(self.config, "STARTUP_CAPITAL_MULTIPLIER", 1.5)

        from simulation.firms import Firm
        active_firms_count = sum(1 for a in simulation.agents.values() if isinstance(a, Firm) and a.is_active)
        
        from simulation.core_agents import Household
        households = [a for a in simulation.agents.values() if isinstance(a, Household) and a.is_active]
        max_firms = max(5, int(len(households) / 15))

        if active_firms_count >= max_firms:
            return # Prevent over-creation of firms (Labor Dilution)

        if active_firms_count < min_firms:
            trigger_probability = 0.5
        else:
            trigger_probability = spirit

        wealthy_households = []
        for h in households:
            if not h.is_active:
                continue

            assets = h.assets
            if isinstance(assets, dict):
                val = assets.get(DEFAULT_CURRENCY, 0.0)
            else:
                try:
                    val = float(assets)
                except (TypeError, ValueError):
                    val = 0.0

            if val > startup_cost * capital_multiplier:
                wealthy_households.append(h)

        for household in wealthy_households:
            if random.random() < trigger_probability:
                self.spawn_firm(simulation, household)
                break  # Max 1 startup per tick
