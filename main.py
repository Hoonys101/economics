import json
import random
import sys
import logging

import config
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.engine import Simulation
from utils.logger import Logger # Import custom Logger
from simulation.ai_model import AITrainingManager
from simulation.decisions.firm_decision_engine import FirmDecisionEngine
from simulation.decisions.household_decision_engine import HouseholdDecisionEngine
from simulation.db.repository import SimulationRepository # Import the repository

custom_logger = Logger() # Instantiate custom Logger
main_logger = logging.getLogger(__name__) # Keep for general logging if needed, but agents will use custom_logger

def load_goods_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_simulation(firm_production_targets=None, initial_firm_inventory_mean=None, output_filename='simulation_results.csv'):
    logging.info("Starting simulation run.", extra={'tags':['setup']})
    
    # Initialize the repository for this simulation run
    repository = SimulationRepository()
    repository.clear_all_data() # Clear previous data

    goods_data = load_goods_data('data/goods.json')
    ai_trainer = AITrainingManager()

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
            "survival_need": config.INITIAL_HOUSEHOLD_NEEDS_MEAN["survival_need"] * (1 + random.uniform(-config.INITIAL_HOUSEHOLD_NEEDS_RANGE, config.INITIAL_HOUSEHOLD_NEEDS_RANGE)),
            "recognition_need": config.INITIAL_HOUSEHOLD_NEEDS_MEAN["recognition_need"] * (1 + random.uniform(-config.INITIAL_HOUSEHOLD_NEEDS_RANGE, config.INITIAL_HOUSEHOLD_NEEDS_RANGE)),
            "growth_need": config.INITIAL_HOUSEHOLD_NEEDS_MEAN["growth_need"] * (1 + random.uniform(-config.INITIAL_HOUSEHOLD_NEEDS_RANGE, config.INITIAL_HOUSEHOLD_NEEDS_RANGE)),
            "wealth_need": config.INITIAL_HOUSEHOLD_NEEDS_MEAN["wealth_need"] * (1 + random.uniform(-config.INITIAL_HOUSEHOLD_NEEDS_RANGE, config.INITIAL_HOUSEHOLD_NEEDS_RANGE)),
            "imitation_need": config.INITIAL_HOUSEHOLD_NEEDS_MEAN["imitation_need"] * (1 + random.uniform(-config.INITIAL_HOUSEHOLD_NEEDS_RANGE, config.INITIAL_HOUSEHOLD_NEEDS_RANGE)),
            "labor_need": config.INITIAL_HOUSEHOLD_NEEDS_MEAN.get("labor_need", 0.0),
            "liquidity_need": initial_liquidity_need
        }
        value_orientation = random.choice(all_value_orientations)
        household_ai_engine = ai_trainer.get_engine(value_orientation)
        household_decision_engine = HouseholdDecisionEngine(ai_engine=household_ai_engine)
        household = Household(id=i, talent=Talent(1.0, {}), goods_data=goods_data, initial_assets=initial_assets, initial_needs=initial_needs, decision_engine=household_decision_engine, value_orientation=value_orientation, ai_engine=household_ai_engine, logger=main_logger)
        
        if i < num_households * 0.1: 
            luxury_food_id = next((g['id'] for g in goods_data if g.get('is_luxury', False)), None)
            if luxury_food_id:
                household.inventory[luxury_food_id] = 10.0
                household.assets += 10.0 * 10.0

        households.append(household)

    firms = []
    use_default_targets = firm_production_targets is None or len(firm_production_targets) != num_firms

    for i in range(num_firms):
        firm_id = i + num_households
        initial_capital = config.INITIAL_FIRM_CAPITAL_MEAN * (1 + random.uniform(-config.INITIAL_FIRM_CAPITAL_RANGE, config.INITIAL_FIRM_CAPITAL_RANGE))
        initial_liquidity_need = config.INITIAL_FIRM_LIQUIDITY_NEED_MEAN * (1 + random.uniform(-config.INITIAL_FIRM_LIQUIDITY_NEED_RANGE, config.INITIAL_FIRM_LIQUIDITY_NEED_RANGE))
        
        targets = config.FIRM_PRODUCTION_TARGETS if use_default_targets else firm_production_targets[i]
        
        firm_decision_engine = FirmDecisionEngine()
        firm = Firm(id=firm_id, initial_capital=initial_capital, initial_liquidity_need=initial_liquidity_need, production_targets=targets, productivity_factor=config.FIRM_PRODUCTIVITY_FACTOR, decision_engine=firm_decision_engine, value_orientation="wealth_and_needs", logger=main_logger)
        
        for good in goods_data:
            firm.inventory[good['id']] = config.INITIAL_FIRM_INVENTORY_MEAN * (1 + random.uniform(-config.INITIAL_FIRM_INVENTORY_RANGE, config.INITIAL_FIRM_INVENTORY_RANGE))
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

    # Pass the repository to the Simulation constructor
    sim = Simulation(households, firms, goods_data, ai_trainer, repository, logger=main_logger)

    if initial_firm_inventory_mean is not None:
        config.INITIAL_FIRM_INVENTORY_MEAN = original_initial_firm_inventory_mean

    for i in range(simulation_ticks):
        # Pass the repository to the run_tick method
        sim.run_tick(repository)
            
    ai_trainer.end_episode(sim.get_all_agents())
    logging.info("Simulation finished. Closing logger.", extra={'tick': sim.time, 'tags': ['shutdown']})

    # Close the repository connection at the end
    sim.close_repository()

if __name__ == '__main__':
    output_filename = 'simulation_results.csv'
    if len(sys.argv) > 1:
        output_filename = sys.argv[1]
    run_simulation(output_filename=output_filename)