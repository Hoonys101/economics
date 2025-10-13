import json
import random
import sys
import logging
from utils.logging_manager import setup_logging, SamplingFilter # Import the new setup function
import config
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.ai.firm_ai import FirmAI
from simulation.engine import Simulation
from simulation.ai_model import AIEngineRegistry
from simulation.ai.state_builder import StateBuilder
from simulation.decisions.action_proposal import ActionProposalEngine
from simulation.decisions.firm_decision_engine import FirmDecisionEngine
from simulation.decisions.household_decision_engine import HouseholdDecisionEngine
from simulation.db_manager import DBManager # Corrected import
from simulation.ai.api import Personality

main_logger = logging.getLogger(__name__)

# --- Setup Logging ---
setup_logging() # Call the setup function

# Get the SamplingFilter instance and set sampling rates
for handler in logging.root.handlers:
    if isinstance(handler, logging.FileHandler):
        for filter_obj in handler.filters:
            if isinstance(filter_obj, SamplingFilter):
                sampling_filter = filter_obj
                break
        else:
            continue
        break
else:
    sampling_filter = None

if sampling_filter:
    sampling_filter.sampling_rates['AIDecision'] = 0.1
    sampling_filter.sampling_rates['ProduceDebug'] = 0.1
    sampling_filter.sampling_rates['FoodConsumptionCalc'] = 0.1
    sampling_filter.sampling_rates['FoodConsumptionControlled'] = 0.1
    sampling_filter.sampling_rates['FoodConsumptionSkipped'] = 0.1
    logging.info("Sampling rates applied to logging.", extra={'tags':['setup']})
else:
    logging.warning("SamplingFilter not found in logging handlers. Sampling rates not applied.", extra={'tags':['setup']})

# --- End Setup Logging ---


def run_simulation(firm_production_targets=None, initial_firm_inventory_mean=None, output_filename='simulation_results.csv'):
    logging.info("Starting simulation run.", extra={'tags':['setup']})
    
    # Initialize the DBManager for this simulation run
    db_manager = DBManager(db_path='simulation_data.db')
    db_manager.reset_database() # Reset for a clean start

    state_builder = StateBuilder()
    action_proposal_engine = ActionProposalEngine(config_module=config)
    ai_trainer = AIEngineRegistry(action_proposal_engine=action_proposal_engine, state_builder=state_builder)

    all_value_orientations = [
        "wealth_and_needs",
        "needs_and_growth",
        "needs_and_social_status"
    ]
    for vo in all_value_orientations:
        ai_trainer.get_engine(vo)

    num_households = config.NUM_HOUSEHOLDS
    num_firms = config.NUM_FIRMS
    simulation_ticks = config.SIMULATION_TICKS

    households = []
    for i in range(num_households):
        initial_assets = config.INITIAL_HOUSEHOLD_ASSETS_MEAN * (1 + random.uniform(-config.INITIAL_HOUSEHOLD_ASSETS_RANGE, config.INITIAL_HOUSEHOLD_ASSETS_RANGE))
        initial_liquidity_need = config.INITIAL_HOUSEHOLD_LIQUIDITY_NEED_MEAN * (1 + random.uniform(-config.INITIAL_HOUSEHOLD_LIQUIDITY_NEED_RANGE, config.INITIAL_HOUSEHOLD_LIQUIDITY_NEED_RANGE))
        initial_needs = {
            "survival": config.INITIAL_HOUSEHOLD_NEEDS_MEAN["survival_need"] * (1 + random.uniform(-config.INITIAL_HOUSEHOLD_NEEDS_RANGE, config.INITIAL_HOUSEHOLD_NEEDS_RANGE)),
            "social": config.INITIAL_HOUSEHOLD_NEEDS_MEAN["recognition_need"] * (1 + random.uniform(-config.INITIAL_HOUSEHOLD_NEEDS_RANGE, config.INITIAL_HOUSEHOLD_NEEDS_RANGE)), # Map recognition_need to social
            "improvement": config.INITIAL_HOUSEHOLD_NEEDS_MEAN["growth_need"] * (1 + random.uniform(-config.INITIAL_HOUSEHOLD_NEEDS_RANGE, config.INITIAL_HOUSEHOLD_NEEDS_RANGE)), # Map growth_need to improvement
            "asset": config.INITIAL_HOUSEHOLD_NEEDS_MEAN["wealth_need"] * (1 + random.uniform(-config.INITIAL_HOUSEHOLD_NEEDS_RANGE, config.INITIAL_HOUSEHOLD_NEEDS_RANGE)), # Map wealth_need to asset
            "imitation_need": config.INITIAL_HOUSEHOLD_NEEDS_MEAN["imitation_need"] * (1 + random.uniform(-config.INITIAL_HOUSEHOLD_NEEDS_RANGE, config.INITIAL_HOUSEHOLD_NEEDS_RANGE)),
            "labor_need": config.INITIAL_HOUSEHOLD_NEEDS_MEAN.get("labor_need", 0.0),
            "liquidity_need": initial_liquidity_need
        }
        value_orientation = random.choice(all_value_orientations)
        
        # Create a random personality
        personality = random.choice(list(Personality))

        # Instantiate HouseholdDecisionEngine, which will internally create and manage HouseholdAI
        household_decision_engine = HouseholdDecisionEngine(agent_id=i, value_orientation=value_orientation, ai_engine_registry=ai_trainer)
        
        household = Household(id=i, talent=Talent(1.0, {}), initial_assets=initial_assets, initial_needs=initial_needs, decision_engine=household_decision_engine, value_orientation=value_orientation, personality=personality, config_module=config, logger=main_logger)
        household.inventory['basic_food'] = config.INITIAL_HOUSEHOLD_FOOD_INVENTORY # Provide initial food (now basic_food)
        
        # Now that the household object is created, set it in the decision engine
        household_decision_engine.set_agent(household)

        # No longer using goods_data for luxury food initialization
        # if i < num_households * 0.1: 
        #     luxury_food_id = next((g['id'] for g in goods_data if g.get('is_luxury', False)), None)
        #     if luxury_food_id:
        #         household.inventory[luxury_food_id] = 10.0
        #         household.assets += 10.0 * 10.0

        households.append(household)

    firms = []
    for i in range(num_firms):
        firm_id = i + num_households
        initial_capital = config.INITIAL_FIRM_CAPITAL_MEAN * (1 + random.uniform(-config.INITIAL_FIRM_CAPITAL_RANGE, config.INITIAL_FIRM_CAPITAL_RANGE))
        initial_liquidity_need = config.INITIAL_FIRM_LIQUIDITY_NEED_MEAN * (1 + random.uniform(-config.INITIAL_FIRM_LIQUIDITY_NEED_RANGE, config.INITIAL_FIRM_LIQUIDITY_NEED_RANGE))
        
        # Assign specialization based on the new config
        specialization = config.FIRM_SPECIALIZATIONS.get(i, "basic_food") # Default to basic_food if not specified

        # Get the AIDecisionEngine for the firm's value orientation
        # Assuming firms also have a value_orientation, for now hardcoding to "wealth_and_needs"
        firm_value_orientation = "wealth_and_needs" # Or get from config/random choice
        ai_decision_engine_instance_firm = ai_trainer.get_engine(firm_value_orientation)

        # Instantiate FirmAI, passing the AIDecisionEngine instance
        firm_ai_instance = FirmAI(
            agent_id=firm_id,
            ai_decision_engine=ai_decision_engine_instance_firm,
            gamma=config.AI_GAMMA,
            epsilon=config.AI_EPSILON,
            base_alpha=config.AI_BASE_ALPHA,
            learning_focus=config.AI_LEARNING_FOCUS
        )
        firm_decision_engine = FirmDecisionEngine(ai_engine=firm_ai_instance, config_module=config)
        
        # Create the Firm instance with specialization instead of production_targets
        firm = Firm(
            id=firm_id, 
            initial_capital=initial_capital, 
            initial_liquidity_need=initial_liquidity_need, 
            specialization=specialization, 
            productivity_factor=config.FIRM_PRODUCTIVITY_FACTOR, 
            decision_engine=firm_decision_engine, 
            value_orientation=firm_value_orientation, 
            config_module=config, 
            logger=main_logger
        )
        
        # Initialize inventory for all possible goods
        for good_name in config.GOODS:
            firm.inventory[good_name] = config.INITIAL_FIRM_INVENTORY_MEAN * (1 + random.uniform(-config.INITIAL_FIRM_INVENTORY_RANGE, config.INITIAL_FIRM_INVENTORY_RANGE))
        firms.append(firm)

    for firm in firms:
        shares_per_household = firm.total_shares / num_households
        for household in households:
            household.shares_owned[firm.id] = shares_per_household

    if initial_firm_inventory_mean is not None:
        original_initial_firm_inventory_mean = config.INITIAL_FIRM_INVENTORY_MEAN
        config.INITIAL_FIRM_INVENTORY_MEAN = initial_firm_inventory_mean

    num_to_employ = int(num_households * config.INITIAL_EMPLOYMENT_RATE)
    unemployed_households = list(households)
    random.shuffle(unemployed_households)

    for firm in firms:
        num_to_hire_per_firm = num_to_employ // len(firms)
        for _ in range(num_to_hire_per_firm):
            if unemployed_households:
                household_to_hire = unemployed_households.pop()
                firm.employees.append(household_to_hire)
                household_to_hire.employer_id = firm.id
                household_to_hire.is_employed = True # Explicitly set is_employed to True
                logging.info(f"Firm {firm.id} initially hired Household {household_to_hire.id}.", extra={'tick': 0, 'agent_id': firm.id, 'tags': ['hiring', 'init']})



    # Pass the db_manager and tracker to the Simulation constructor
    sim = Simulation(households, firms, ai_trainer, db_manager, config_module=config, logger=main_logger)

    if initial_firm_inventory_mean is not None:
        config.INITIAL_FIRM_INVENTORY_MEAN = original_initial_firm_inventory_mean

    for i in range(simulation_ticks):
        # Pass the repository to the run_tick method
        sim.run_tick()
            
    ai_trainer.end_episode(sim.get_all_agents())
    logging.info("Simulation finished. Closing logger.", extra={'tick': sim.time, 'tags': ['shutdown']})

    # Close the DBManager connection at the end
    sim.finalize_simulation()

if __name__ == '__main__':
    output_filename = 'simulation_results.csv'
    if len(sys.argv) > 1:
        output_filename = sys.argv[1]
    run_simulation(output_filename=output_filename)