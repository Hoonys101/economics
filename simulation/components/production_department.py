from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging
import math
import simulation
import random

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.dtos.config_dtos import FirmConfigDTO
from modules.system.api import DEFAULT_CURRENCY

logger = logging.getLogger(__name__)

class ProductionDepartment:
    """Handles the production logic for a firm."""

    def __init__(self, firm: Firm, config: FirmConfigDTO):
        self.firm = firm
        self.config = config

    def produce(self, current_time: int, technology_manager: Any = None) -> float:
        """
        Cobb-Douglas 생산 함수를 사용한 생산 로직.
        Phase 21: Modified Cobb-Douglas with Automation.
        """
        try:
            # [EARLY EXIT]
            if len(self.firm.hr.employees) == 0:
                if simulation.logger:
                    simulation.logger.log_thought(
                        tick=current_time,
                        agent_id=str(self.firm.id),
                        action="PRODUCE",
                        decision="HALT",
                        reason="NO_EMPLOYEES",
                        context={}
                    )
                return 0.0

            log_extra = {"tick": current_time, "agent_id": self.firm.id, "tags": ["production"]}

            # 1. 감가상각 처리
            depreciation_rate = self.config.capital_depreciation_rate
            self.firm.capital_stock *= (1.0 - depreciation_rate)

            # Phase 21: Automation Decay
            self.firm.automation_level *= 0.995 # Slow decay (0.5% per tick)
            if self.firm.automation_level < 0.001: self.firm.automation_level = 0.0

            # 2. 노동 및 자본 투입량 계산
            # SoC Refactor: Get total labor skill from HR
            total_labor_skill = self.firm.hr.get_total_labor_skill()

            # 3. Cobb-Douglas Parameters
            base_alpha = self.config.labor_alpha
            automation_reduction = self.config.automation_labor_reduction

            # Phase 21: Adjusted Alpha
            # alpha_adjusted = base_alpha * (1 - automation_level * 0.5)
            # If Automation = 1.0, Alpha = 0.7 * 0.5 = 0.35 (Capital dependent)
            alpha_raw = base_alpha * (1.0 - (self.firm.automation_level * automation_reduction))
            alpha_adjusted = max(self.config.labor_elasticity_min, alpha_raw)
            beta_adjusted = 1.0 - alpha_adjusted

            # Effective Labor & Capital
            capital = max(self.firm.capital_stock, 0.01)

            # Technology Multiplier (WO-053)
            tfp = self.firm.productivity_factor  # Total Factor Productivity

            if technology_manager:
                tfp *= technology_manager.get_productivity_multiplier(self.firm.id)

            # Phase 15: Quality Calculation
            avg_skill = self.firm.hr.get_avg_skill()

            item_config = self.config.goods.get(self.firm.specialization, {})
            quality_sensitivity = item_config.get("quality_sensitivity", 0.5)
            actual_quality = self.firm.base_quality + (math.log1p(avg_skill) * quality_sensitivity)

            produced_quantity = 0.0
            if total_labor_skill > 0 and capital > 0:
                produced_quantity = tfp * (total_labor_skill ** alpha_adjusted) * (capital ** beta_adjusted)

            actual_produced = 0.0
            if produced_quantity > 0:
                # WO-030: Input Constraints Logic
                input_config = self.config.goods.get(self.firm.specialization, {}).get("inputs", {})

                if input_config:
                    max_by_inputs = float('inf')
                    for mat, req_per_unit in input_config.items():
                        available = self.firm.input_inventory.get(mat, 0.0)
                        if req_per_unit > 0:
                            max_by_inputs = min(max_by_inputs, available / req_per_unit)

                    # Constrain production
                    actual_produced = min(produced_quantity, max_by_inputs)

                    # Deduct used inputs
                    for mat, req_per_unit in input_config.items():
                        amount_to_deduct = actual_produced * req_per_unit
                        self.firm.input_inventory[mat] = max(0.0, self.firm.input_inventory.get(mat, 0.0) - amount_to_deduct)
                else:
                    actual_produced = produced_quantity

                if actual_produced > 0:
                    self.firm.add_inventory(self.firm.specialization, actual_produced, actual_quality)

            # ThoughtStream: Instrument halted production
            if actual_produced == 0.0 and simulation.logger:
                 reason = "UNKNOWN"
                 context = {}

                 # 2. Check Liquidity (Wage Bill)
                 wage_bill = 0.0
                 for employee in self.firm.hr.employees:
                     base = self.firm.hr.employee_wages.get(employee.id, 0.0)
                     wage = self.firm.hr.calculate_wage(employee, base)
                     wage_bill += wage

                 # Refactor: Use finance.balance instead of firm.assets
                 # Fix: Handle Dict[CurrencyCode, float] vs float comparison
                 cash_balance = self.firm.finance.balance.get(DEFAULT_CURRENCY, 0.0)
                 if cash_balance < wage_bill:
                     reason = "LIQUIDITY_CRUNCH"
                     context = {"cash": cash_balance, "wage_bill": wage_bill}

                 # 3. Check Input Shortage
                 elif produced_quantity > 0:
                     # If we theoretically could produce (labor & capital > 0) but actual is 0
                     input_config = self.config.goods.get(self.firm.specialization, {}).get("inputs", {})
                     if input_config:
                         for mat, req in input_config.items():
                             if req > 0 and self.firm.input_inventory.get(mat, 0.0) == 0:
                                  reason = "INPUT_SHORTAGE"
                                  context = {"input_inventory": self.firm.input_inventory.copy()}
                                  break

                 # 4. Check Overstock
                 if reason == "UNKNOWN":
                     target = self.firm.production_target
                     current_inv = self.firm.inventory.get(self.firm.specialization, 0.0)
                     if current_inv > target * 2.0:
                          reason = "OVERSTOCK"
                          context = {"inventory": current_inv, "target": target}

                 if reason != "UNKNOWN":
                     simulation.logger.log_thought(
                        tick=current_time,
                        agent_id=str(self.firm.id),
                        action="PRODUCE",
                        decision="HALT",
                        reason=reason,
                        context=context
                     )

            return actual_produced

        except Exception as e:
            import traceback
            logger.error(f'FIRM_CRASH_PREVENTED | Firm {self.firm.id}: {e}')
            logger.debug(traceback.format_exc())
            return 0.0

    def add_capital(self, amount: float) -> None:
        """Increases the firm's capital stock."""
        self.firm.capital_stock += amount

    def set_automation_level(self, level: float) -> None:
        """Sets the firm's automation level (0.0 to 1.0)."""
        self.firm.automation_level = max(0.0, min(1.0, level))

    def set_production_target(self, quantity: float) -> None:
        """Sets the production target."""
        self.firm.production_target = quantity
        self.firm.logger.info(f"INTERNAL_EXEC | Firm {self.firm.id} set production target to {self.firm.production_target:.1f}")

    def invest_in_automation(self, amount: float, government: Any) -> bool:
        """
        Invests in automation.
        Delegates payment to Finance, handles state update here.
        """
        if self.firm.finance.invest_in_automation(amount, government):
            cost_per_pct = self.config.automation_cost_per_pct
            if cost_per_pct > 0:
                gained_a = (amount / cost_per_pct) / 100.0
                self.set_automation_level(self.firm.automation_level + gained_a)
                self.firm.logger.info(f"INTERNAL_EXEC | Firm {self.firm.id} invested {amount:.1f} in automation.")
            return True
        return False

    def invest_in_capex(self, amount: float, government: Any) -> bool:
        """
        Invests in Capital Expenditure (CAPEX).
        Delegates payment to Finance, handles state update here.
        """
        if self.firm.finance.invest_in_capex(amount, government):
            efficiency = 1.0 / self.config.capital_to_output_ratio
            added_capital = amount * efficiency
            self.add_capital(added_capital)
            self.firm.logger.info(f"INTERNAL_EXEC | Firm {self.firm.id} invested {amount:.1f} in CAPEX.")
            return True
        return False

    def invest_in_rd(self, amount: float, government: Any, current_time: int) -> bool:
        """
        Invests in Research & Development (R&D).
        Delegates payment to Finance, handles state update (probabilistic outcome) here.
        """
        if self.firm.finance.invest_in_rd(amount, government):
            self._execute_rd_outcome(amount, current_time)
            return True
        return False

    def _execute_rd_outcome(self, budget: float, current_time: int) -> None:
        """Executes the probabilistic outcome of R&D investment."""
        self.firm.research_history["total_spent"] += budget

        # Revenue logic should be via finance
        revenue_usd = self.firm.finance.revenue_this_turn.get(simulation.DEFAULT_CURRENCY, 0.0)
        denominator = max(revenue_usd * 0.2, 100.0)
        base_chance = min(1.0, budget / denominator)

        avg_skill = 1.0
        if self.firm.hr.employees:
            avg_skill = sum(getattr(e, 'labor_skill', 1.0) for e in self.firm.hr.employees) / len(self.firm.hr.employees)

        success_chance = base_chance * avg_skill

        if random.random() < success_chance:
            self.firm.research_history["success_count"] += 1
            self.firm.research_history["last_success_tick"] = current_time
            self.firm.base_quality += 0.05
            self.firm.productivity_factor *= 1.05
            self.firm.logger.info(f"INTERNAL_EXEC | Firm {self.firm.id} R&D SUCCESS (Budget: {budget:.1f})")
