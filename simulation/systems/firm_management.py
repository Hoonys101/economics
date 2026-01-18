from __future__ import annotations
import logging
import random
from typing import TYPE_CHECKING, Optional, Dict, Any

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

    def __init__(self, config_module: Any):
        self.config = config_module

    def spawn_firm(self, simulation: "Simulation", founder_household: "Household") -> Optional["Firm"]:
        """
        Wealthy households found new firms.
        """
        startup_cost = getattr(self.config, "STARTUP_COST", 30000.0)

        # 1. Capital Deduction
        if founder_household.assets < startup_cost:
            return None
        founder_household.assets -= startup_cost

        # 2. Generate New Firm ID
        max_id = max([a.id for a in simulation.agents.values()], default=0)
        new_firm_id = max_id + 1

        # 3. Choose Specialization (Blue Ocean Strategy)
        specializations = list(self.config.GOODS.keys())
        is_visionary = False
        
        mutation_rate = getattr(self.config, "VISIONARY_MUTATION_RATE", 0.05)
        if random.random() < mutation_rate:
            is_visionary = True
            
        if is_visionary:
            active_specs = {f.specialization for f in simulation.firms if f.is_active}
            potential_blue_oceans = [s for s in specializations if s not in active_specs]
            
            if potential_blue_oceans:
                specialization = random.choice(potential_blue_oceans)
            else:
                specialization = random.choice(specializations)
        else:
            specialization = random.choice(specializations)
            
        goods_config = self.config.GOODS.get(specialization, {})
        sector = goods_config.get("sector", "OTHER")

        has_inputs = bool(goods_config.get("inputs"))
        if has_inputs:
             startup_cost *= 1.5

        # 4. AI Setup
        from simulation.ai.firm_ai import FirmAI
        from simulation.ai.service_firm_ai import ServiceFirmAI
        from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
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

        firm_decision_engine = AIDrivenFirmDecisionEngine(firm_ai, self.config, simulation.logger)

        # 5. Create Firm
        instance_class = ServiceFirm if is_service else Firm
        new_firm = instance_class(
            id=new_firm_id,
            initial_capital=startup_cost,
            initial_liquidity_need=getattr(self.config, "INITIAL_FIRM_LIQUIDITY_NEED_MEAN", 50.0),
            specialization=specialization,
            productivity_factor=random.uniform(8.0, 12.0),
            decision_engine=firm_decision_engine,
            value_orientation=value_orientation,
            config_module=self.config,
            logger=simulation.logger,
            sector=sector,
            is_visionary=is_visionary,
        )
        
        new_firm.founder_id = founder_household.id
        if "loan_market" in simulation.markets:
            new_firm.decision_engine.loan_market = simulation.markets["loan_market"]

        # 6. Add to Simulation
        simulation.firms.append(new_firm)
        simulation.agents[new_firm.id] = new_firm

        if simulation.stock_market:
            new_firm.init_ipo(simulation.stock_market)

        logger.info(
            f"STARTUP | Household {founder_household.id} founded Firm {new_firm_id} "
            f"(Specialization: {specialization}, Capital: {startup_cost})"
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

        active_firms_count = sum(1 for f in simulation.firms if f.is_active)
        max_firms = max(5, int(len(simulation.households) / 15))

        if active_firms_count >= max_firms:
            return # Prevent over-creation of firms (Labor Dilution)

        if active_firms_count < min_firms:
            trigger_probability = 0.5
        else:
            trigger_probability = spirit

        wealthy_households = [
            h for h in simulation.households
            if h.is_active and h.assets > startup_cost * capital_multiplier
        ]

        for household in wealthy_households:
            if random.random() < trigger_probability:
                self.spawn_firm(simulation, household)
                break  # Max 1 startup per tick
