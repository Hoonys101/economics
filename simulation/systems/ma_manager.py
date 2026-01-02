from typing import List, Dict, Any, TYPE_CHECKING
import logging
import random

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.db.repository import SimulationRepository
    from simulation.engine import Simulation
    
class MAManager:
    """
    Manages Mergers, Acquisitions, and Bankruptcy (Liquidation).
    Runs periodically within the simulation engine.
    """
    def __init__(self, simulation: "Simulation", config_module: Any):
        self.simulation = simulation
        self.config = config_module
        self.logger = logging.getLogger("MAManager")
        self.ma_enabled = getattr(config_module, "MA_ENABLED", True)
        self.bankruptcy_loss_threshold = getattr(config_module, "BANKRUPTCY_CONSECUTIVE_LOSS_TICKS", 20)

    def process_market_exits_and_entries(self, current_tick: int):
        """
        Main entry point.
        1. Identify M&A (Predator vs Prey).
        2. Identify Bankruptcy (Capital < 0 or Consecutive Losses).
        """
        if not self.ma_enabled:
            return

        # 1. Identify Predators and Preys
        firms = self.simulation.firms
        if not firms:
            return

        # Calculate stats for relative thresholds
        avg_assets = sum(f.assets for f in firms) / len(firms)
        
        predators = []
        preys = []
        bankrupts = []

        for firm in firms:
            # Update Valuation first
            firm.calculate_valuation()
            
            # Bankruptcy Criteria
            if firm.assets < 0:
                bankrupts.append(firm)
                continue
            
            if firm.consecutive_loss_turns >= self.bankruptcy_loss_threshold:
                 # High risk of bankruptcy -> Prey priority
                 preys.append(firm)
            elif firm.assets < avg_assets * 0.2: # Low capital -> Prey
                preys.append(firm)
            
            # Predator Criteria
            if firm.assets > avg_assets * 1.5 and firm.current_profit > 0:
                predators.append(firm)

        # 2. M&A Matching Loop
        # Shuffle to prevent deterministic bias
        random.shuffle(predators)
        random.shuffle(preys)
        
        surviving_preys = [] # Preys that were NOT acquired (risk bankruptcy)
        
        active_preys = [p for p in preys if p not in bankrupts] # Don't buy already bankrupt firms (too risky?) or cheap?
        # Actually acquiring a bankrupt firm is valid if asset > debt.
        # But for simplicity, let's say checked bankrupts are doomed unless acquired.
        # Let's add bankrupts to potential targets too?
        # No, let's keep it simple: Bankrupts die unless acquired?
        # For this version: Bankrupts die immediately. Preys are Struggling but Alive.
        
        for prey in active_preys:
            acquired = False
            for predator in predators:
                if predator.id == prey.id:
                    continue
                
                # Check if Predator can afford
                target_valuation = prey.valuation
                offer_price = target_valuation * 1.1 # 10% Premium
                
                # Check Cash Requirement
                min_cash_ratio = getattr(self.config, "MIN_ACQUISITION_CASH_RATIO", 1.5)
                if predator.assets >= offer_price * min_cash_ratio:
                    # Attempt Deal
                    self._execute_merger(predator, prey, offer_price, current_tick)
                    acquired = True
                    predators.remove(predator) # One deal per tick per predator?
                    break
            
            if not acquired:
                surviving_preys.append(prey)
                
        # 3. Process Bankruptcies (Liquidation)
        for firm in bankrupts:
            # Check if recently acquired? (No, we removed them from list if acquired)
            # Actually we didn't include bankrupts in M&A list above.
            self._execute_bankruptcy(firm, current_tick)

    def _execute_merger(self, predator: "Firm", prey: "Firm", price: float, tick: int):
        self.logger.info(f"M&A_EVENT | Predator {predator.id} acquires Prey {prey.id}. Price: {price:,.2f}. Prey Valuation: {prey.valuation:,.2f}")
        
        # 1. Payment
        predator.assets -= price
        # Distribute price to shareholders? (Simplification: Disappears from simulation or goes to 'Households' abstractly)
        # In this model, we don't track specific shareholder lookup easily yet. 
        # So we assume cash goes to "Economy" (Households) via dividends or just buy-out.
        # Ideally, `prey.founder_id` gets it?
        if prey.founder_id is not None and prey.founder_id in self.simulation.households_dict:
             self.simulation.households_dict[prey.founder_id].assets += price
        
        # 2. Asset Transfer
        # Capital Stock (Machines)
        predator.capital_stock += prey.capital_stock
        
        # Inventory
        for item, qty in prey.inventory.items():
            predator.inventory[item] = predator.inventory.get(item, 0.0) + qty
            
        # Employees (Absorb or Fire?)
        # Let's say 50% retained, 50% fired (Efficiency)
        retained_count = 0
        fired_count = 0
        for emp in list(prey.employees):
            if random.random() < 0.5:
                # Fire
                emp.quit(tick)
                fired_count += 1
            else:
                # Retain (Transfer)
                prey.employees.remove(emp)
                predator.employees.append(emp)
                # Wage? Keep same or reset? Keep same for now.
                predator.employee_wages[emp.id] = prey.employee_wages.get(emp.id, 10.0)
                emp.employer_id = predator.id
                retained_count += 1
                
        self.logger.info(f"M&A_RESULT | Retained {retained_count} employees, Fired {fired_count}.")
        
        # 3. Deactivate Prey
        prey.is_active = False 
        # Mark for removal in engine?
        # Engine needs to clean up inactive firms.
        pass

    def _execute_bankruptcy(self, firm: "Firm", tick: int):
        recovered = firm.liquidate_assets()
        self.logger.info(f"BANKRUPTCY | Firm {firm.id} liquidated. Recovered Cash: {recovered:,.2f}. Debt unpaid if neg.")
        
        # Fire all employees
        for emp in list(firm.employees):
            emp.quit(tick)
            
        firm.is_active = False
