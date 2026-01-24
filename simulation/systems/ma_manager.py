from typing import List, Dict, Any, TYPE_CHECKING
import logging
import random

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
        hostile_targets = [] # Phase 21
        bankrupts = []

        for firm in firms:
            # Update Valuation first
            firm.calculate_valuation()
            
            # Bankruptcy Criteria
            if firm.assets < 0:
                bankrupts.append(firm)
                continue
            
            # Standard Distress (Friendly M&A)
            # SoC Refactor: use finance.consecutive_loss_turns
            if firm.finance.consecutive_loss_turns >= self.bankruptcy_loss_threshold:
                 preys.append(firm)
            elif firm.assets < avg_assets * 0.2:
                preys.append(firm)
            
            # Phase 21: Hostile Takeover Criteria
            # Target if Market Cap < Intrinsic Value * Threshold
            intrinsic_value = firm.valuation # Based on calculate_valuation (Net Assets + Profit Premium)
            # Spec says: Market Cap < Intrinsic * 0.7
            # Note: firm.valuation might ALREADY be intrinsic value.
            # Market Cap is different. Market Cap = Stock Price * Shares.
            # Firm.get_market_cap uses book value if no stock price.
            # But let's assume we use 'stock_price' if available.
            # If firm is public.

            market_cap = firm.get_market_cap()
            # If market cap is low relative to assets...
            # Note: calculate_valuation uses profit premium.
            # Intrinsic Value here roughly equals 'valuation'.

            threshold = getattr(self.config, "HOSTILE_TAKEOVER_DISCOUNT_THRESHOLD", 0.7)

            if market_cap < intrinsic_value * threshold:
                hostile_targets.append(firm)

            # Predator Criteria
            # Must have System 2 Planner and expansion mode == 'MA'?
            # Or just be rich.
            # Phase 21 Spec: Predator Assets > Target Market Cap * 1.5.
            # Let's filter later. Just identify rich firms.
            # SoC Refactor: use finance.current_profit
            if firm.assets > avg_assets * 1.5 and firm.finance.current_profit > 0:
                predators.append(firm)

        # 2. M&A Matching Loop
        random.shuffle(predators)
        
        # Merge lists, prioritize Hostile Targets for Predators who are GROWTH_HACKERs?
        # Let's process Hostile first, then Friendly.
        
        # --- Hostile Takeover Loop ---
        for predator in list(predators): # Copy list to iterate
            # Check strategy
            expansion_mode = "ORGANIC"
            if hasattr(predator, "system2_planner") and predator.system2_planner:
                guidance = predator.system2_planner.cached_guidance
                expansion_mode = guidance.get("expansion_mode", "ORGANIC")

            # Only Aggressive predators do Hostile Takeovers?
            # Or rich ones. Spec: "Predator Assets > Target Market Cap * 1.5"

            target_found = False
            for target in hostile_targets:
                if target.id == predator.id: continue
                if target in bankrupts: continue # Don't hostile takeover a bankrupt firm (waste)

                # Check Capacity
                target_mcap = target.get_market_cap()
                if predator.assets > target_mcap * 1.5:
                    # Attempt Hostile Takeover
                    success = self._attempt_hostile_takeover(predator, target, target_mcap, current_tick)
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
                target_valuation = prey.valuation
                offer_price = target_valuation * 1.1 # 10% Premium
                
                # Check Cash Requirement
                min_cash_ratio = getattr(self.config, "MIN_ACQUISITION_CASH_RATIO", 1.5)
                if predator.assets >= offer_price * min_cash_ratio:
                    # Attempt Deal
                    self._execute_merger(predator, prey, offer_price, current_tick, is_hostile=False)
                    acquired = True
                    predators.remove(predator)
                    break
            
        # 3. Process Bankruptcies (Liquidation)
        for firm in bankrupts:
            if firm.is_active: # Check if not acquired already (though unlikely in loop structure)
                self._execute_bankruptcy(firm, current_tick)

    def _attempt_hostile_takeover(self, predator: "Firm", target: "Firm", market_cap: float, tick: int) -> bool:
        """
        Phase 21: Probabilistic Hostile Takeover.
        """
        # Offer Premium
        offer_price = market_cap * 1.2 # 20% Premium over market price

        # Success Probability
        # Base 60%
        success_prob = 0.6

        # Roll
        if random.random() < success_prob:
            self.logger.info(f"HOSTILE_TAKEOVER_SUCCESS | Predator {predator.id} seizes Target {target.id}. Offer: {offer_price:,.2f}")
            self._execute_merger(predator, target, offer_price, tick, is_hostile=True)
            return True
        else:
            self.logger.info(f"HOSTILE_TAKEOVER_FAIL | Target {target.id} fended off Predator {predator.id}.")
            return False

    def _execute_merger(self, predator: "Firm", prey: "Firm", price: float, tick: int, is_hostile: bool = False):
        tag = "HOSTILE_MERGER" if is_hostile else "FRIENDLY_MERGER"

        self.logger.info(f"{tag}_EXECUTE | Predator {predator.id} acquires Prey {prey.id}. Price: {price:,.2f}.")
        
        # 1. Payment
        # predator.assets -= price

        # Pay Shareholders (Households)
        # Assuming 100% buyout.
        # Ideally iterate shareholders.
        # For simplicity, pay founder or distribute generally?
        # Let's stick to paying founder as proxy for 'Shareholders'
        if prey.founder_id is not None and prey.founder_id in self.simulation.agents:
             target_agent = self.simulation.agents[prey.founder_id]
             if hasattr(self.simulation, 'settlement_system') and self.simulation.settlement_system:
                 self.simulation.settlement_system.transfer(predator, target_agent, price, f"M&A Acquisition {prey.id}")
             else:
                 predator.withdraw(price)
                 target_agent.deposit(price)
        else:
             # If no owner found, transfer to government (state capture)
             # This policy (State Capture) ensures zero-sum integrity when owner is missing.
             if hasattr(self.simulation, 'settlement_system') and self.simulation.settlement_system:
                 self.simulation.settlement_system.transfer(predator, self.simulation.government, price, f"M&A Acquisition {prey.id} (State)")
             else:
                 predator.withdraw(price)
                 self.simulation.government.deposit(price)
        
        # 2. Asset Transfer
        # SoC Refactor: use production.add_capital
        predator.production.add_capital(prey.capital_stock)
        
        # Phase 21: Transfer Automation Tech?
        # If prey has higher automation, predator learns?
        # Or just average?
        # Let's say Predator keeps their own logic, maybe slight boost if Prey was advanced.
        if hasattr(prey, "automation_level") and hasattr(predator, "automation_level"):
            if prey.automation_level > predator.automation_level:
                new_level = (predator.automation_level + prey.automation_level) / 2.0
                predator.production.set_automation_level(new_level)

        # Inventory
        for item, qty in prey.inventory.items():
            predator.inventory[item] = predator.inventory.get(item, 0.0) + qty
            
        # Employees
        retained_count = 0
        fired_count = 0

        # Hostile Takeovers often have deeper cuts
        retention_rate = 0.3 if is_hostile else 0.5

        # SoC Refactor: use hr.employees and hr.hire
        for emp in list(prey.hr.employees):
            if random.random() > retention_rate:
                # Fire
                emp.quit()
                fired_count += 1
            else:
                # Retain
                prey.hr.remove_employee(emp)
                wage = prey.hr.employee_wages.get(emp.id, 10.0)
                predator.hr.hire(emp, wage)
                emp.employer_id = predator.id
                retained_count += 1
                
        self.logger.info(f"{tag}_RESULT | Retained {retained_count}, Fired {fired_count}.")
        
        # 3. Deactivate Prey
        prey.is_active = False 

    def _execute_bankruptcy(self, firm: "Firm", tick: int):
        recovered = firm.liquidate_assets()
        self.logger.info(f"BANKRUPTCY | Firm {firm.id} liquidated. Recovered Cash: {recovered:,.2f}.")

        # 2. [NEW] Record the asset destruction in the central ledger.
        # This is the core change to fix the money leak.
        if hasattr(self.simulation, 'settlement_system') and self.simulation.settlement_system:
            self.simulation.settlement_system.record_liquidation_loss(
                firm=firm,
                amount=recovered,
                tick=tick
            )
        else:
            # Fallback or error if the settlement system is missing
            self.logger.error(f"CRITICAL: SettlementSystem not found. Liquidation loss of {recovered} for Firm {firm.id} is NOT RECORDED.")
        
        # SoC Refactor: use hr.employees
        for emp in list(firm.hr.employees):
            emp.quit()
            
        firm.is_active = False
