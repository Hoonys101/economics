from typing import List, Dict, Any, Optional
import logging

from simulation.models import Order, Transaction
from simulation.core_agents import Household # Household 클래스 임포트
from simulation.base_agent import BaseAgent
from simulation.decisions.firm_decision_engine import FirmDecisionEngine # FirmDecisionEngine 임포트

logger = logging.getLogger(__name__)

class Firm(BaseAgent):
    """기업 주체. 생산과 고용의 주체."""
    def __init__(self, id: int, initial_capital: float, initial_liquidity_need: float, production_targets: Dict[str, float], productivity_factor: float, decision_engine: FirmDecisionEngine, value_orientation: str, initial_inventory: Optional[Dict[str, float]] = None, loan_market: Any = None, logger: Any = None) -> None:
        super().__init__(id, initial_capital, {"liquidity_need": initial_liquidity_need}, decision_engine, value_orientation, name=f"Firm_{id}", logger=logger)
        if initial_inventory is not None:
            self.inventory.update(initial_inventory)
        self.employees: List[Household] = []
        self.consecutive_loss_turns: int = 0
        self.current_profit: float = 0.0
        self.revenue_this_turn: float = 0.0
        self.cost_this_turn: float = 0.0
        self.current_production: float = 0.0
        self.production_targets: Dict[str, float] = production_targets
        self.productivity_factor: float = productivity_factor
        self.total_shares: float = 100.0
        self.last_prices: Dict[str, float] = {}
        self.hires_last_tick: int = 0

        self.decision_engine.loan_market = loan_market

    def distribute_dividends(self, households: List[Household]) -> List[Transaction]:
        import config
        transactions = []
        distributable_profit = max(0, self.current_profit * config.DIVIDEND_RATE)

        if distributable_profit > 0:
            for household in households:
                shares = household.shares_owned.get(self.id, 0.0)
                if shares > 0:
                    dividend_amount = distributable_profit * (shares / self.total_shares)
                    transactions.append(Transaction(buyer_id=household.id, seller_id=self.id, item_id="dividend", quantity=dividend_amount, price=1.0, transaction_type="dividend"))
                    self.logger.info(f"Firm {self.id} distributed {dividend_amount:.2f} dividend to Household {household.id}.", extra={'tick': self.time, 'agent_id': self.id, 'household_id': household.id, 'amount': dividend_amount, 'tags': ['dividend']})

        self.current_profit = 0.0
        self.revenue_this_turn = 0.0
        self.cost_this_turn = 0.0
        return transactions

    def make_decision(self, market_data: Dict[str, Any], current_time: int) -> List[Order]:
        log_extra = {'tick': current_time, 'agent_id': self.id, 'tags': ['firm_action']}
        self.logger.debug(f"FIRM_DECISION_START | Firm {self.id} before decision: Assets={self.assets:.2f}, Employees={len(self.employees)}, is_active={self.is_active}", extra={**log_extra, 'assets_before': self.assets, 'num_employees_before': len(self.employees), 'is_active_before': self.is_active})
        decisions = self.decision_engine.make_decisions(self, current_time, market_data)
        self.logger.debug(f"FIRM_DECISION_END | Firm {self.id} after decision: Assets={self.assets:.2f}, Employees={len(self.employees)}, is_active={self.is_active}, Decisions={len(decisions)}", extra={**log_extra, 'assets_after': self.assets, 'num_employees_after': len(self.employees), 'is_active_after': self.is_active, 'num_decisions': len(decisions)})
        return decisions

    def produce(self, current_time: int) -> None:
        log_extra = {'tick': current_time, 'agent_id': self.id, 'tags': ['production']}
        
        # Debugging employee labor skills
        employee_details = []
        for employee in self.employees:
            employee_details.append(f"ID: {employee.id}, Labor Skill: {employee.labor_skill}")
        self.logger.debug(f"Firm {self.id} employees details: [{'; '.join(employee_details)}]", extra={**log_extra, 'employee_details': employee_details})

        total_labor_skill = sum(employee.labor_skill for employee in self.employees)
        self.logger.info(f"Starting production. Total labor skill: {total_labor_skill:.1f}, Number of employees: {len(self.employees)}, Productivity Factor: {self.productivity_factor:.2f}", extra={**log_extra, 'total_labor_skill': total_labor_skill, 'num_employees': len(self.employees), 'productivity_factor': self.productivity_factor})
        self.current_production = 0.0
        
        for item_id, target_quantity in self.production_targets.items():
            self.logger.debug(f"Production target for {item_id}: {target_quantity:.1f}", extra={**log_extra, 'item_id': item_id, 'target_quantity': target_quantity})
            current_inventory = self.inventory.get(item_id, 0)
            self.logger.debug(f"Item: {item_id}, Inventory BEFORE production: {current_inventory:.1f}", extra={**log_extra, 'item_id': item_id, 'current_inventory': current_inventory})
            if current_inventory < target_quantity:
                needed_quantity = target_quantity - current_inventory
                self.logger.debug(f"Item: {item_id}, Needed quantity: {needed_quantity:.1f}", extra={**log_extra, 'item_id': item_id, 'needed_quantity': needed_quantity})
                
                produced_quantity = min(needed_quantity, total_labor_skill * self.productivity_factor)
                self.logger.debug(f"Item: {item_id}, Produced quantity: {produced_quantity:.1f} (calculated from {total_labor_skill:.1f} * {self.productivity_factor:.2f})", extra={**log_extra, 'item_id': item_id, 'produced_quantity': produced_quantity, 'calculated_from_labor_and_productivity': f"{total_labor_skill:.1f} * {self.productivity_factor:.2f}"})
                
                if produced_quantity > 0:
                    self.inventory[item_id] = current_inventory + produced_quantity
                    self.current_production += produced_quantity
                    self.logger.info(f"Produced {produced_quantity:.1f} of {item_id}. New inventory: {self.inventory[item_id]:.1f}", extra={**log_extra, 'item_id': item_id, 'produced_quantity': produced_quantity, 'new_inventory': self.inventory[item_id]})
                    self.logger.debug(f"Item: {item_id}, Inventory AFTER production: {self.inventory[item_id]:.1f}", extra={**log_extra, 'item_id': item_id, 'inventory_after_production': self.inventory[item_id]})
            else:
                self.logger.debug(f"Item: {item_id}, Inventory ({current_inventory:.1f}) >= Target ({target_quantity:.1f}). No production needed.", extra={**log_extra, 'item_id': item_id, 'current_inventory': current_inventory, 'target_quantity': target_quantity})

    def update_needs(self, current_time: int) -> None:
        import config
        log_extra = {'tick': current_time, 'agent_id': self.id, 'tags': ['firm_needs']}
        self.logger.debug(f"FIRM_NEEDS_UPDATE_START | Firm {self.id} needs before update: Liquidity={self.needs["liquidity_need"]:.1f}, Assets={self.assets:.2f}, Employees={len(self.employees)}", extra={**log_extra, 'needs_before': self.needs, 'assets_before': self.assets, 'num_employees_before': len(self.employees)})

        inventory_value = sum(self.inventory.values())
        holding_cost = inventory_value * config.INVENTORY_HOLDING_COST_RATE
        self.assets -= holding_cost
        self.cost_this_turn += holding_cost
        if holding_cost > 0:
            self.logger.info(f"Paid inventory holding cost: {holding_cost:.2f}", extra={**log_extra, 'holding_cost': holding_cost})

        self.needs["liquidity_need"] += config.LIQUIDITY_NEED_INCREASE_RATE
        self.needs["liquidity_need"] = min(100.0, self.needs["liquidity_need"])

        if self.current_profit < 0:
            self.consecutive_loss_turns += 1
        else:
            self.consecutive_loss_turns = 0

        if self.assets <= config.ASSETS_CLOSURE_THRESHOLD or \
           self.consecutive_loss_turns >= config.FIRM_CLOSURE_TURNS_THRESHOLD:
            self.is_active = False
            self.logger.warning(f"FIRM_INACTIVE | Firm {self.id} closed down. Assets: {self.assets:.2f}, Consecutive Loss Turns: {self.consecutive_loss_turns}", extra={{**log_extra, 'assets': self.assets, 'consecutive_loss_turns': self.consecutive_loss_turns, 'tags': ['firm_closure']}})
        self.logger.debug(f"FIRM_NEEDS_UPDATE_END | Firm {self.id} needs after update: Liquidity={self.needs["liquidity_need"]:.1f}, Assets={self.assets:.2f}, Employees={len(self.employees)}, is_active={self.is_active}", extra={**log_extra, 'needs_after': self.needs, 'assets_after': self.assets, 'num_employees_after': len(self.employees), 'is_active_after': self.is_active})