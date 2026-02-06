import random
import logging
import sys
from typing import Dict, Any
from pathlib import Path

import config
from modules.common.config.impl import ConfigManagerImpl
from simulation.utils.config_factory import create_config_dto
from simulation.dtos.config_dtos import HouseholdConfigDTO, FirmConfigDTO
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.ai.firm_ai import FirmAI
from simulation.engine import Simulation
from simulation.ai_model import AIEngineRegistry
from simulation.ai.state_builder import StateBuilder
from simulation.decisions.action_proposal import ActionProposalEngine
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.decisions.rule_based_firm_engine import RuleBasedFirmDecisionEngine
from simulation.decisions.rule_based_household_engine import RuleBasedHouseholdDecisionEngine
from simulation.decisions.ai_driven_household_engine import (
    AIDrivenHouseholdDecisionEngine,
)
from simulation.ai.api import Personality
from simulation.ai.household_ai import HouseholdAI
from simulation.db.repository import SimulationRepository
from simulation.initialization.initializer import SimulationInitializer

logger = logging.getLogger(__name__)

def create_simulation(overrides: Dict[str, Any] = None) -> Simulation:
    """Create simulation instance with optional config overrides."""
    logger.info("Initializing simulation.", extra={"tags": ["setup"]})

    if overrides:
        for key, value in overrides.items():
            setattr(config, key, value)

    # Seed for reproducibility
    if hasattr(config, "RANDOM_SEED"):
         random.seed(config.RANDOM_SEED)

    # Initialize the SimulationRepository for this simulation run
    repository = SimulationRepository()
    repository.clear_all_data()  # Clear existing data for a clean start

    # Initialize ConfigManager
    config_manager = ConfigManagerImpl(Path("config"), legacy_config=config)

    if overrides:
        if "SIMULATION_ACTIVE_SCENARIO" in overrides:
            config_manager.set_value_for_test("simulation.active_scenario", overrides["SIMULATION_ACTIVE_SCENARIO"])

    # Create Config DTOs
    hh_config_dto = create_config_dto(config, HouseholdConfigDTO)
    firm_config_dto = create_config_dto(config, FirmConfigDTO)

    state_builder = StateBuilder()
    action_proposal_engine = ActionProposalEngine(config_module=config_manager)
    ai_trainer = AIEngineRegistry(
        action_proposal_engine=action_proposal_engine, state_builder=state_builder
    )

    all_value_orientations = [
        "wealth_and_needs",
        "needs_and_growth",
        "needs_and_social_status",
    ]
    for vo in all_value_orientations:
        ai_trainer.get_engine(vo)

    num_households = config.NUM_HOUSEHOLDS
    num_firms = config.NUM_FIRMS

    goods_data = [
        {"id": good_name, **good_attrs}
        for good_name, good_attrs in config.GOODS.items()
    ]
    households = []
    initial_balances: Dict[int, float] = {}  # WO-124: Collect intended initial balances

    # Reserve IDs 0-99 for System Agents (CentralBank, Government, Bank, etc)
    # Households start at 100
    START_ID_HOUSEHOLDS = 100

    for i in range(num_households):
        agent_id = START_ID_HOUSEHOLDS + i
        agent_id = START_ID_HOUSEHOLDS + i
        initial_assets = config.INITIAL_HOUSEHOLD_ASSETS_MEAN * (
            1
            + random.uniform(
                -config.INITIAL_HOUSEHOLD_ASSETS_RANGE,
                config.INITIAL_HOUSEHOLD_ASSETS_RANGE,
            )
        )
        initial_balances[agent_id] = initial_assets  # Record intended balance

        initial_liquidity_need = config.INITIAL_HOUSEHOLD_LIQUIDITY_NEED_MEAN * (
            1
            + random.uniform(
                -config.INITIAL_HOUSEHOLD_LIQUIDITY_NEED_RANGE,
                config.INITIAL_HOUSEHOLD_LIQUIDITY_NEED_RANGE,
            )
        )
        initial_needs = {
            "survival": config.INITIAL_HOUSEHOLD_NEEDS_MEAN["survival_need"]
            * (
                1
                + random.uniform(
                    -config.INITIAL_HOUSEHOLD_NEEDS_RANGE,
                    config.INITIAL_HOUSEHOLD_NEEDS_RANGE,
                )
            ),
            "social": config.INITIAL_HOUSEHOLD_NEEDS_MEAN["recognition_need"]
            * (
                1
                + random.uniform(
                    -config.INITIAL_HOUSEHOLD_NEEDS_RANGE,
                    config.INITIAL_HOUSEHOLD_NEEDS_RANGE,
                )
            ),  # Map recognition_need to social
            "improvement": config.INITIAL_HOUSEHOLD_NEEDS_MEAN["growth_need"]
            * (
                1
                + random.uniform(
                    -config.INITIAL_HOUSEHOLD_NEEDS_RANGE,
                    config.INITIAL_HOUSEHOLD_NEEDS_RANGE,
                )
            ),  # Map growth_need to improvement
            "asset": config.INITIAL_HOUSEHOLD_NEEDS_MEAN["wealth_need"]
            * (
                1
                + random.uniform(
                    -config.INITIAL_HOUSEHOLD_NEEDS_RANGE,
                    config.INITIAL_HOUSEHOLD_NEEDS_RANGE,
                )
            ),  # Map wealth_need to asset
            "imitation_need": config.INITIAL_HOUSEHOLD_NEEDS_MEAN["imitation_need"]
            * (
                1
                + random.uniform(
                    -config.INITIAL_HOUSEHOLD_NEEDS_RANGE,
                    config.INITIAL_HOUSEHOLD_NEEDS_RANGE,
                )
            ),
            "labor_need": config.INITIAL_HOUSEHOLD_NEEDS_MEAN.get("labor_need", 0.0),
            "liquidity_need": initial_liquidity_need,
        }
        value_orientation = random.choice(all_value_orientations)

        # Create a random personality
        personality = random.choice(list(Personality))

        # Instantiate HouseholdAI
        ai_decision_engine_instance = ai_trainer.get_engine(value_orientation)
        household_ai_instance = HouseholdAI(agent_id=agent_id, ai_decision_engine=ai_decision_engine_instance)

        # Instantiate HouseholdDecisionEngine with the HouseholdAI instance and config_module
        # Check config for decision engine preference
        hh_engine_type = getattr(config, "HOUSEHOLD_DECISION_ENGINE", "AI_DRIVEN")
        if hh_engine_type == "RULE_BASED":
             household_decision_engine = RuleBasedHouseholdDecisionEngine(config_module=config_manager, logger=logger)
        else:
             household_decision_engine = AIDrivenHouseholdDecisionEngine(
                ai_engine=household_ai_instance, config_module=config_manager
             )

        # Generate Risk Aversion (0.1 ~ 10.0)
        # Assuming Normal Distribution centered at 1.0, or Uniform as per spec "Random Gaussian or Uniform"
        # Let's use Log-Normalish or just Uniform [0.1, 10.0] as explicitly stated range.
        # Spec: "0.1 (Gambler) to 10.0 (Super Conservative)"
        risk_aversion = random.uniform(0.1, 10.0)

        household = Household(
            id=agent_id,
            talent=Talent(max(0.5, random.gauss(1.0, 0.2)), {}), # WO-023-B: The Lottery of Birth
            goods_data=goods_data,
            initial_assets=0.0,  # WO-124: Start empty (Genesis Protocol)
            initial_assets_record=initial_assets, # Record "birthright" for history
            initial_needs=initial_needs,
            decision_engine=household_decision_engine,
            value_orientation=value_orientation,
            personality=personality,
            config_dto=hh_config_dto,
            risk_aversion=risk_aversion,
            logger=logger,
        )
        household._econ_state.inventory["basic_food"] = (
            config.INITIAL_HOUSEHOLD_FOOD_INVENTORY
        )  # Provide initial food (now basic_food)

        households.append(household)

    firms = []
    START_ID_FIRMS = START_ID_HOUSEHOLDS + num_households

    for i in range(num_firms):
        firm_id = START_ID_FIRMS + i
        initial_capital = config.INITIAL_FIRM_CAPITAL_MEAN * (
            1
            + random.uniform(
                -config.INITIAL_FIRM_CAPITAL_RANGE, config.INITIAL_FIRM_CAPITAL_RANGE
            )
        )
        initial_balances[firm_id] = initial_capital  # Record intended capital

        initial_liquidity_need = config.INITIAL_FIRM_LIQUIDITY_NEED_MEAN * (
            1
            + random.uniform(
                -config.INITIAL_FIRM_LIQUIDITY_NEED_RANGE,
                config.INITIAL_FIRM_LIQUIDITY_NEED_RANGE,
            )
        )

        # Assign specialization based on the new config
        specialization = config.FIRM_SPECIALIZATIONS.get(
            i, "basic_food"
        )  # Default to basic_food if not specified

        # Get the AIDecisionEngine for the firm's value orientation
        # Assuming firms also have a value_orientation, for now hardcoding to "wealth_and_needs"
        firm_value_orientation = "wealth_and_needs"  # Or get from config/random choice
        ai_decision_engine_instance_firm = ai_trainer.get_engine(firm_value_orientation)

        # Instantiate FirmAI, passing the AIDecisionEngine instance
        firm_ai_instance = FirmAI(
            agent_id=firm_id,
            ai_decision_engine=ai_decision_engine_instance_firm,
            gamma=config.AI_GAMMA,
            epsilon=config.AI_EPSILON,
            base_alpha=config.AI_BASE_ALPHA,
            learning_focus=config.AI_LEARNING_FOCUS,
        )

        # Check config for decision engine preference
        engine_type = getattr(config, "FIRM_DECISION_ENGINE", "AI_DRIVEN")
        if engine_type == "RULE_BASED":
             firm_decision_engine = RuleBasedFirmDecisionEngine(config_module=config_manager, logger=logger)
        else:
             firm_decision_engine = AIDrivenFirmDecisionEngine(
                ai_engine=firm_ai_instance, config_module=config_manager
             )

        # Create the Firm instance with specialization instead of production_targets
        firm = Firm(
            id=firm_id,
            initial_capital=0.0,  # WO-124: Start empty (Genesis Protocol)
            initial_liquidity_need=initial_liquidity_need,
            specialization=specialization,
            productivity_factor=config.FIRM_PRODUCTIVITY_FACTOR,
            decision_engine=firm_decision_engine,
            value_orientation=firm_value_orientation,
            config_dto=firm_config_dto,
            logger=logger,
        )

        # Initialize inventory for all possible goods
        for good_name in config.GOODS:
            qty = config.INITIAL_FIRM_INVENTORY_MEAN * (
                1
                + random.uniform(
                    -config.INITIAL_FIRM_INVENTORY_RANGE,
                    config.INITIAL_FIRM_INVENTORY_RANGE,
                )
            )
            firm.add_item(good_name, qty)
        firms.append(firm)

    firm_founders = {}
    for firm in firms:
        # Phase 14-1: Assign a Single Founder (Owner) logic
        # For simplicity in Genesis, assign randomly or round-robin
        # Let's use round-robin to ensure distribution
        founder_household = households[firm.id % num_households]
        firm.owner_id = founder_household.id
        firm.founder_id = founder_household.id

        # Add to portfolio
        # Portfolio is now a Portfolio object in _econ_state
        pass

        firm_founders[firm.id] = founder_household.id

        # Removed legacy share distribution. Firms hold 100% treasury shares initially.
        # Registration in StockMarket is handled by Simulation.init_ipo.

    num_to_employ = int(num_households * config.INITIAL_EMPLOYMENT_RATE)
    unemployed_households = list(households)
    random.shuffle(unemployed_households)

    for firm in firms:
        num_to_hire_per_firm = num_to_employ // len(firms)
        for _ in range(num_to_hire_per_firm):
            if unemployed_households:
                household_to_hire = unemployed_households.pop()
                firm.hr.employees.append(household_to_hire)
                household_to_hire._econ_state.employer_id = firm.id
                household_to_hire._econ_state.is_employed = (
                    True  # Explicitly set is_employed to True
                )
                household_to_hire._econ_state.current_wage = config.INITIAL_WAGE
                firm.hr.employee_wages[household_to_hire.id] = config.INITIAL_WAGE
                logger.info(
                    f"Firm {firm.id} initially hired Household {household_to_hire.id}.",
                    extra={"tick": 0, "agent_id": firm.id, "tags": ["hiring", "init"]},
                )

    # Use the new SimulationInitializer
    initializer = SimulationInitializer(
        config_manager=config_manager,
        config_module=config,
        goods_data=goods_data,
        repository=repository,
        logger=logger,
        households=households,
        firms=firms,
        ai_trainer=ai_trainer,
        initial_balances=initial_balances, # WO-124: Pass Genesis distribution map
    )
    sim = initializer.build_simulation()

    return sim
