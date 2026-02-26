from typing import List, Dict, Any, TYPE_CHECKING
import logging
import random
from modules.finance.api import IMonetaryAuthority
from modules.system.api import DEFAULT_CURRENCY
from modules.finance.utils.currency_math import round_to_pennies

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.db.repository import SimulationRepository
    from simulation.engine import Simulation
    from simulation.ai.firm_system2_planner import FirmSystem2Planner
    
class MAManager:
    """
    Manages Mergers, Acquisitions, and Bankruptcy (Liquidation).
    Runs periodically within the simulation engine.
    Phase 21: Added Hostile Takeover Logic.
    """
    def __init__(self, simulation: "Simulation", config_module: Any, settlement_system: IMonetaryAuthority = None):
        self.simulation = simulation
        self.config = config_module
        self.logger = logging.getLogger("MAManager")
        self.ma_enabled = getattr(config_module, "MA_ENABLED", True)
        self.bankruptcy_loss_threshold = getattr(config_module, "BANKRUPTCY_CONSECUTIVE_LOSS_TICKS", 20)

        # Inject or fallback
        if settlement_system:
             self.settlement_system = settlement_system
        elif isinstance(simulation.settlement_system, IMonetaryAuthority):
             self.settlement_system = simulation.settlement_system
        else:
             self.logger.warning("MAManager: SettlementSystem not provided or does not satisfy IMonetaryAuthority!")
             self.settlement_system = None

    def _get_balance(self, firm: "Firm") -> float:
        return firm.wallet.get_balance(DEFAULT_CURRENCY)

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
        # Refactor: Use finance.balance
        avg_assets = sum(self._get_balance(f) for f in firms) / len(firms)
        
        predators = []
        preys = []
        hostile_targets = [] # Phase 21
        bankrupts = []

        for firm in firms:
            # Update Valuation first
            firm.calculate_valuation()
            
            # Bankruptcy Criteria
            # Refactor: Use finance.balance
            firm_balance = self._get_balance(firm)

            if firm_balance < 0:
                bankrupts.append(firm)
                continue
            
            # Standard Distress (Friendly M&A)
            if firm.finance_state.consecutive_loss_turns >= self.bankruptcy_loss_threshold:
                 preys.append(firm)
            elif firm_balance < avg_assets * 0.2:
                preys.append(firm)
            
            # Phase 21: Hostile Takeover Criteria
            # FIXED: Intrinsic value should be in pennies for consistent comparison with market_cap (pennies)
            intrinsic_value_pennies = firm.finance_state.valuation_pennies

            market_cap_pennies = firm.get_market_cap()
            threshold = getattr(self.config, "HOSTILE_TAKEOVER_DISCOUNT_THRESHOLD", 0.7)

            if market_cap_pennies < intrinsic_value_pennies * threshold:
                hostile_targets.append(firm)

            # Predator Criteria
            if firm_balance > avg_assets * 1.5 and firm.finance_state.current_profit.get(DEFAULT_CURRENCY, 0) > 0:
                predators.append(firm)

        # 2. M&A Matching Loop
        random.shuffle(predators)
        
        # --- Hostile Takeover Loop ---
        hostile_premium = getattr(self.config, "HOSTILE_TAKEOVER_PREMIUM", 1.2)
        friendly_premium = getattr(self.config, "FRIENDLY_MERGER_PREMIUM", 1.1)

        for predator in list(predators): # Copy list to iterate
            # Check strategy
            expansion_mode = "ORGANIC"
            if hasattr(predator, "system2_planner") and predator.system2_planner:
                guidance = predator.system2_planner.cached_guidance
                expansion_mode = guidance.get("expansion_mode", "ORGANIC")

            target_found = False
            for target in hostile_targets:
                if target.id == predator.id: continue
                if target in bankrupts: continue

                # Check Capacity
                target_mcap_pennies = target.get_market_cap()
                if self._get_balance(predator) > target_mcap_pennies * 1.5:
                    # Attempt Hostile Takeover
                    # MIGRATION: Pass market_cap (pennies)
                    success = self._attempt_hostile_takeover(predator, target, target_mcap_pennies, current_tick)
                    if success:
                        target_found = True
                        if target in preys: preys.remove(target)
                        if target in hostile_targets: hostile_targets.remove(target)
                        break

            if target_found:
                predators.remove(predator)

        # --- Friendly M&A Loop (Existing Logic) ---
        active_preys = [p for p in preys if p not in bankrupts and p.is_active]
        
        for prey in active_preys:
            acquired = False
            for predator in predators:
                if predator.id == prey.id:
                    continue
                
                # Check if Predator can afford
                target_valuation = prey.valuation # int pennies
                offer_price_float = target_valuation * friendly_premium
                offer_price_pennies = round_to_pennies(offer_price_float)
                
                # Check Cash Requirement
                min_cash_ratio = getattr(self.config, "MIN_ACQUISITION_CASH_RATIO", 1.5)
                if self._get_balance(predator) >= offer_price_pennies * min_cash_ratio:
                    # Attempt Deal
                    self._execute_merger(predator, prey, offer_price_pennies, current_tick, is_hostile=False)
                    acquired = True
                    predators.remove(predator)
                    break
            
        # 3. Process Bankruptcies (Liquidation)
        for firm in bankrupts:
            if firm.is_active:
                self._execute_bankruptcy(firm, current_tick)

    def _attempt_hostile_takeover(self, predator: "Firm", target: "Firm", market_cap: float, tick: int) -> bool:
        """
        Phase 21: Probabilistic Hostile Takeover.
        """
        # Offer Premium
        premium = getattr(self.config, "HOSTILE_TAKEOVER_PREMIUM", 1.2)

        # market_cap is in pennies (float), convert to int pennies for settlement
        offer_price_float = market_cap * premium
        offer_price_pennies = round_to_pennies(offer_price_float)

        # Success Probability
        success_prob = getattr(self.config, "HOSTILE_TAKEOVER_SUCCESS_PROB", 0.6)

        # Roll
        if random.random() < success_prob:
            self.logger.info(f"HOSTILE_TAKEOVER_SUCCESS | Predator {predator.id} seizes Target {target.id}. Offer: {offer_price_float:,.2f}")
            self._execute_merger(predator, target, offer_price_pennies, tick, is_hostile=True)
            return True
        else:
            self.logger.info(f"HOSTILE_TAKEOVER_FAIL | Target {target.id} fended off Predator {predator.id}.")
            return False

    def _execute_merger(self, predator: "Firm", prey: "Firm", price: int, tick: int, is_hostile: bool = False):
        tag = "HOSTILE_MERGER" if is_hostile else "FRIENDLY_MERGER"

        self.logger.info(f"{tag}_EXECUTE | Predator {predator.id} acquires Prey {prey.id}. Price: {price} pennies.")
        
        # 1. Payment
        # Replaced direct withdrawal with settlement transfer
        if prey.founder_id is not None and prey.founder_id in self.simulation.agents:
             target_agent = self.simulation.agents[prey.founder_id]
             if self.settlement_system:
                 self.settlement_system.transfer(predator, target_agent, price, f"M&A Acquisition {prey.id}", tick=tick)
        else:
             # State Capture
             if self.settlement_system:
                 self.settlement_system.transfer(predator, self.simulation.government, price, f"M&A Acquisition {prey.id} (State)", tick=tick)
        
        # 2. Asset Transfer
        predator.capital_stock += prey.capital_stock
        
        if hasattr(prey, "automation_level") and hasattr(predator, "automation_level"):
            if prey.automation_level > predator.automation_level:
                new_level = (predator.automation_level + prey.automation_level) / 2.0
                predator.automation_level = new_level

        # Inventory
        for item, qty in prey.get_all_items().items():
            predator.add_item(item, qty)
            
        # Employees
        retained_count = 0
        fired_count = 0

        retention_rates = getattr(self.config, "MERGER_EMPLOYEE_RETENTION_RATES", [0.3, 0.5])
        # [0] = Hostile, [1] = Friendly
        retention_rate = retention_rates[0] if is_hostile else retention_rates[1]

        for emp in list(prey.hr_state.employees):
            if random.random() > retention_rate:
                # Fire
                emp.quit()
                fired_count += 1
            else:
                # Retain
                prey.hr_engine.remove_employee(prey.hr_state, emp)
                wage = prey.hr_state.employee_wages.get(emp.id, 10.0)
                predator.hr_engine.hire(predator.hr_state, emp, wage, tick)
                emp.employer_id = predator.id
                retained_count += 1
                
        self.logger.info(f"{tag}_RESULT | Retained {retained_count}, Fired {fired_count}.")
        
        # 3. Deactivate Prey
        prey.is_active = False 

    def _execute_bankruptcy(self, firm: "Firm", tick: int):
        # 1. Calculate values of real assets before they are wiped
        inv_value_pennies = 0
        # Simple estimation: default price if no market data, or look up market
        default_price = 10.0
        if self.simulation.markets:
             for item, qty in firm.get_all_items().items():
                 price = default_price
                 if item in self.simulation.markets:
                     m = self.simulation.markets[item]
                     if hasattr(m, "avg_price"): price = m.avg_price
                 # Convert to pennies
                 inv_value_pennies += round_to_pennies(qty * price * 100) # Assuming price is dollars

        capital_value_pennies = round_to_pennies(firm.capital_stock * 100) # Assuming 1 unit of capital = $1 ? Or verify?
        # Typically capital_stock is value in dollars or units.
        # If it's value, we treat as dollars. If units, we need a price.
        # Assuming value in dollars for now as per previous logic.

        # 2. Liquidate (Wipe assets, return cash)
        # recovered_assets is Dict[CurrencyCode, int]
        recovered_assets = firm.liquidate_assets(current_tick=tick)
        recovered_cash_pennies = sum(recovered_assets.values())

        self.logger.info(f"BANKRUPTCY | Firm {firm.id} liquidated. Cash Remaining: {recovered_cash_pennies} pennies.")

        # 3. Record Liquidation of Real Assets
        if self.settlement_system:
            # WO-178: Escheatment Logic
            government = getattr(self.simulation, "government", None)

            self.settlement_system.record_liquidation(
                agent=firm,
                inventory_value=inv_value_pennies,
                capital_value=capital_value_pennies,
                recovered_cash=0, # WO-018: Real assets written off, not sold
                reason="bankruptcy_real_assets",
                tick=tick,
                government_agent=government
            )
        else:
            self.logger.error(f"CRITICAL: SettlementSystem not found. Liquidation loss for Firm {firm.id} is NOT RECORDED.")

        # 4. Escheat Cash to Government (State Capture) - Handled by record_liquidation
        
        # 5. Clear Employees
        for emp in list(firm.hr_state.employees):
            emp.quit()
            
        firm.is_active = False
