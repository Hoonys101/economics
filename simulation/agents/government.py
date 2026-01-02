import logging
import math
from typing import Dict, List, Any, Deque
from collections import deque

logger = logging.getLogger(__name__)

class Government:
    """
    정부 에이전트. 세금을 징수하고 보조금을 지급하거나 인프라에 투자합니다.
    """

    def __init__(self, id: int, initial_assets: float = 0.0, config_module: Any = None):
        self.id = id
        self.assets = initial_assets
        self.config_module = config_module
        
        self.total_collected_tax: float = 0.0
        self.total_spent_subsidies: float = 0.0
        self.infrastructure_level: int = 0
        
        # 세수 유형별 집계
        self.tax_revenue: Dict[str, float] = {}

        # History buffers for visualization
        self.tax_history: List[Dict[str, Any]] = [] # For Stacked Bar Chart (breakdown per tick)
        self.welfare_history: List[Dict[str, float]] = [] # For Welfare Line Chart
        self.history_window_size = 50

        # Current tick accumulators (reset every tick)
        self.current_tick_stats = {
            "tax_revenue": {},
            "welfare_spending": 0.0,
            "stimulus_spending": 0.0,
            "total_collected": 0.0
        }

        # Flow Tracking
        self.revenue_this_tick = 0.0
        self.expenditure_this_tick = 0.0
        self.revenue_breakdown_this_tick = {}

        # 성향 및 욕구 (AI 훈련용 더미)
        self.value_orientation = "public_service"
        self.needs: Dict[str, float] = {}

        # GDP Tracking for Stimulus
        self.gdp_history: List[float] = [] # Stores total_production per tick
        self.gdp_history_window = 20 # 2 quarters (approx 20 ticks based on spec saying 2 quarters)

        # Policy State
        self.approval_rating = 0.50
        self.income_tax_rate = getattr(self.config_module, "INCOME_TAX_RATE", 0.1)
        self.tax_brackets = getattr(self.config_module, "TAX_BRACKETS", []).copy()

        logger.info(
            f"Government {self.id} initialized with assets: {self.assets}",
            extra={"tick": 0, "agent_id": self.id, "tags": ["init", "government"]},
        )

    def calculate_approval_rating(self, households: List[Any]) -> float:
        """
        Calculates approval rating based on Survival, Relative, Future, and Tax scores.
        Formula: Score = (S_survival * w1) + (S_relative * w2) + (S_future * w3) - (S_tax * w4 * P_sen)
        """
        approvals = 0
        total = 0

        # Weights (Configurable)
        w1 = 1.0 # Survival
        w2 = 0.5 # Relative (Inequality)
        w3 = 0.5 # Future (Growth)
        w4 = 2.0 # Tax (Pain)

        # Pre-calculate averages for Relative Score
        active_households = [h for h in households if h.is_active]
        if not active_households:
            return 0.0

        avg_assets = sum(h.assets for h in active_households) / len(active_households)

        # Calculate GDP Growth for Future Score
        gdp_growth_rate = 0.0
        if len(self.gdp_history) >= 2:
            prev_gdp = self.gdp_history[-2]
            if prev_gdp > 0:
                gdp_growth_rate = (self.gdp_history[-1] - prev_gdp) / prev_gdp

        s_future = gdp_growth_rate * 10.0

        survival_cost = self.config_module.SURVIVAL_COST if hasattr(self.config_module, "SURVIVAL_COST") else 10.0

        for h in active_households:
            # 1. Survival Score
            if h.is_employed:
                wage = getattr(h, "current_wage", 0.0)
                s_survival = min((wage / (survival_cost + 1e-9)) - 1, 1.0)
            else:
                benefit = survival_cost * getattr(self.config_module, "UNEMPLOYMENT_BENEFIT_RATIO", 0.7)
                s_survival = min((benefit / (survival_cost + 1e-9)) - 1, 0.0)

            # 2. Relative Score
            s_relative = math.log((h.assets / (avg_assets + 1e-9)) + math.e)

            # 3. Tax Score
            s_tax = self.income_tax_rate

            # 4. Personality Sensitivity
            p_sen = 1.0
            personality = getattr(h, "personality", None)
            if personality:
                p_str = str(personality)
                if "MISER" in p_str:
                    p_sen = 1.5
                elif "SOCIAL" in p_str or "STATUS_SEEKER" in p_str:
                    p_sen = 0.8

            # Total Score
            score = (s_survival * w1) + (s_relative * w2) + (s_future * w3) - (s_tax * w4 * p_sen)

            if score > 0:
                approvals += 1
            total += 1

        if total == 0:
            return 0.0

        self.approval_rating = approvals / total
        return self.approval_rating

    def adjust_fiscal_policy(self, households: List[Any], current_gdp: float, inflation_rate: float):
        """
        Adjusts tax rates and distributes dividends based on approval rating and fiscal rules.
        """
        # 1. Update Approval Rating
        self.calculate_approval_rating(households)

        # 2. Citizen Dividend (Liquidity Recycling)
        target_reserve = current_gdp * 0.10
        excess_cash = self.assets - target_reserve

        # Inflation Check (if > 5%, halt distribution)
        inflation_warning = inflation_rate > 0.05

        if excess_cash > 0 and not inflation_warning:
            payout = excess_cash * 0.3 # Dampened distribution
            active_households = [h for h in households if h.is_active]

            if active_households:
                per_capita = payout / len(active_households)
                for h in active_households:
                    # provide_subsidy handles asset transfer and logging/stats
                    self.provide_subsidy(h, per_capita, 0)

                logger.info(
                    f"CITIZEN_DIVIDEND | Distributed {payout:.2f} total (Per Capita: {per_capita:.2f})",
                    extra={"tick": 0, "agent_id": self.id, "tags": ["fiscal", "dividend"]}
                )

        # 3. Tax Rate Adjustment (Political Response)
        tax_mode = getattr(self.config_module, "TAX_MODE", "PROGRESSIVE")

        change = 0.0
        if self.approval_rating < 0.40:
            change = -0.01 # Lower Tax
        elif self.approval_rating > 0.60:
            change = 0.01 # Raise Tax

        if change != 0.0:
            # Update flat rate
            self.income_tax_rate = max(0.05, min(0.50, self.income_tax_rate + change))

            # Update Progressive Brackets if applicable
            if tax_mode == "PROGRESSIVE" and self.tax_brackets:
                new_brackets = []
                for threshold, rate in self.tax_brackets:
                    if rate > 0:
                        new_rate = max(0.05, min(0.60, rate + change))
                        new_brackets.append((threshold, new_rate))
                    else:
                        new_brackets.append((threshold, rate))
                self.tax_brackets = new_brackets

            logger.info(
                f"FISCAL_ADJUSTMENT | Approval: {self.approval_rating:.2f} -> Tax Rate Adjusted by {change} (Base: {self.income_tax_rate:.2f})",
                extra={"tick": 0, "agent_id": self.id, "tags": ["fiscal", "tax_rate"]}
            )

    def calculate_income_tax(self, income: float, survival_cost: float) -> float:
        """
        Calculates income tax based on TAX_MODE (FLAT or PROGRESSIVE).
        """
        tax_mode = getattr(self.config_module, "TAX_MODE", "PROGRESSIVE")

        if tax_mode == "FLAT":
            return income * self.income_tax_rate

        # Progressive Logic
        brackets = self.tax_brackets if self.tax_brackets else getattr(self.config_module, "TAX_BRACKETS", [])

        if not brackets:
            return income * self.income_tax_rate

        tax_total = 0.0
        remaining_income = income
        previous_limit_abs = 0.0

        for multiple, rate in brackets:
            limit_abs = multiple * survival_cost

            upper_bound = min(income, limit_abs)
            lower_bound = max(0, previous_limit_abs)

            taxable_amount = max(0.0, upper_bound - lower_bound)

            if taxable_amount > 0:
                tax_total += taxable_amount * rate

            if income <= limit_abs:
                break

            previous_limit_abs = limit_abs

        return tax_total

    def reset_tick_flow(self):
        """
        매 틱 시작 시 호출되어 이번 틱의 Flow 데이터를 초기화하고,
        이전 틱의 데이터를 History에 저장합니다.
        """
        if getattr(self, "revenue_breakdown_this_tick", None) is None:
             self.revenue_breakdown_this_tick = {}

        # Reset Logic
        self.revenue_this_tick = 0.0
        self.expenditure_this_tick = 0.0
        self.revenue_breakdown_this_tick = {}

    def collect_tax(self, amount: float, tax_type: str, source_id: int, current_tick: int):
        """세금을 징수합니다."""
        if amount <= 0:
            return 0.0
            
        self.assets += amount
        self.total_collected_tax += amount
        self.revenue_this_tick += amount
        
        # 세목별 집계 (Cumulative)
        self.tax_revenue[tax_type] = self.tax_revenue.get(tax_type, 0.0) + amount

        # Current Tick Stats
        self.current_tick_stats["tax_revenue"][tax_type] = self.current_tick_stats["tax_revenue"].get(tax_type, 0.0) + amount
        self.current_tick_stats["total_collected"] += amount

        logger.info(
            f"TAX_COLLECTED | Collected {amount:.2f} as {tax_type} from {source_id}",
            extra={
                "tick": current_tick,
                "agent_id": self.id,
                "amount": amount,
                "tax_type": tax_type,
                "source_id": source_id,
                "tags": ["tax", "revenue"]
            }
        )
        return amount

    def provide_subsidy(self, target_agent: Any, amount: float, current_tick: int):
        """보조금을 지급합니다."""
        if self.assets < amount:
            amount = max(0.0, self.assets)
            
        if amount <= 0:
            return 0.0
            
        self.assets -= amount
        self.total_spent_subsidies += amount
        self.expenditure_this_tick += amount

        target_agent.assets += amount
        
        self.current_tick_stats["welfare_spending"] += amount

        logger.info(
            f"SUBSIDY_PAID | Paid {amount:.2f} subsidy to {target_agent.id}",
            extra={
                "tick": current_tick,
                "agent_id": self.id,
                "amount": amount,
                "target_id": target_agent.id,
                "tags": ["subsidy", "expenditure"]
            }
        )
        return amount

    def get_survival_cost(self, market_data: Dict[str, Any]) -> float:
        """ Calculates current survival cost based on food prices. """
        avg_food_price = 0.0
        goods_market = market_data.get("goods_market", {})
        if "basic_food_current_sell_price" in goods_market:
            avg_food_price = goods_market["basic_food_current_sell_price"]
        else:
            avg_food_price = getattr(self.config_module, "GOODS_INITIAL_PRICE", {}).get("basic_food", 5.0)

        daily_food_need = getattr(self.config_module, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 1.0)
        return max(avg_food_price * daily_food_need, 10.0)

    def run_welfare_check(self, agents: List[Any], market_data: Dict[str, Any], current_tick: int):
        """
        Phase 4: Performs welfare checks, wealth tax collection, and stimulus injection.
        Called every tick by the Engine.
        """
        # 1. Calculate Survival Cost (Dynamic)
        survival_cost = self.get_survival_cost(market_data)

        # 2. Wealth Tax & Unemployment Benefit
        wealth_tax_rate_annual = getattr(self.config_module, "ANNUAL_WEALTH_TAX_RATE", 0.02)
        ticks_per_year = getattr(self.config_module, "TICKS_PER_YEAR", 100.0)
        wealth_tax_rate_tick = wealth_tax_rate_annual / ticks_per_year
        wealth_threshold = getattr(self.config_module, "WEALTH_TAX_THRESHOLD", 50000.0)

        unemployment_ratio = getattr(self.config_module, "UNEMPLOYMENT_BENEFIT_RATIO", 0.8)
        benefit_amount = survival_cost * unemployment_ratio

        total_wealth_tax = 0.0
        total_welfare_paid = 0.0

        for agent in agents:
            if not getattr(agent, "is_active", False):
                continue

            if hasattr(agent, "needs") and hasattr(agent, "is_employed"):

                # A. Wealth Tax
                net_worth = agent.assets
                stock_value = 0.0
                if hasattr(agent, "shares_owned") and agent.shares_owned:
                    stock_market_data = market_data.get("stock_market", {})
                    for firm_id, qty in agent.shares_owned.items():
                         key = f"stock_{firm_id}"
                         if key in stock_market_data:
                             stock_value += qty * stock_market_data[key]["avg_price"]

                total_assets = agent.assets + stock_value

                if total_assets > wealth_threshold:
                    tax_amount = (total_assets - wealth_threshold) * wealth_tax_rate_tick
                    if agent.assets >= tax_amount:
                        agent.assets -= tax_amount
                        self.collect_tax(tax_amount, "wealth_tax", agent.id, current_tick)
                        total_wealth_tax += tax_amount
                    else:
                        taken = agent.assets
                        agent.assets = 0
                        self.collect_tax(taken, "wealth_tax", agent.id, current_tick)
                        total_wealth_tax += taken

                # B. Unemployment Benefit
                if not agent.is_employed:
                    if self.assets < benefit_amount:
                        self.assets += benefit_amount # Print money
                        logger.info(f"DEFICIT_SPENDING | Government printed {benefit_amount:.2f} for welfare.", extra={"tick": current_tick, "agent_id": self.id})

                    self.provide_subsidy(agent, benefit_amount, current_tick)
                    total_welfare_paid += benefit_amount

        # 3. Stimulus Check (Helicopter Money)
        current_gdp = market_data.get("total_production", 0.0)
        self.gdp_history.append(current_gdp)
        if len(self.gdp_history) > self.gdp_history_window:
            self.gdp_history.pop(0)

        trigger_drop = getattr(self.config_module, "STIMULUS_TRIGGER_GDP_DROP", -0.05)

        should_stimulus = False
        if len(self.gdp_history) >= 10:
            past_gdp = self.gdp_history[-10]
            if past_gdp > 0:
                change = (current_gdp - past_gdp) / past_gdp
                if change <= trigger_drop:
                    should_stimulus = True

        if should_stimulus:
             stimulus_amount = survival_cost * 5.0
             active_households = [a for a in agents if hasattr(a, "is_employed") and getattr(a, "is_active", False)]

             total_stimulus = 0.0
             for h in active_households:
                 if self.assets < stimulus_amount:
                     self.assets += stimulus_amount # Print
                 self.provide_subsidy(h, stimulus_amount, current_tick)
                 total_stimulus += stimulus_amount

             logger.warning(
                 f"STIMULUS_TRIGGERED | GDP Drop Detected. Paid {total_stimulus:.2f} total.",
                 extra={"tick": current_tick, "agent_id": self.id, "gdp_current": current_gdp}
             )

    def update_monetary_policy(self, bank_agent: Any, current_tick: int, inflation_rate: float = 0.0):
        """
        중앙은행 역할: 인플레이션 등에 따라 기준 금리를 조절합니다.
        (현재는 간단한 Rule-based 로직: 인플레가 높으면 금리 인상)
        """
        self.reset_tick_flow()

        current_rate = bank_agent.base_rate
        target_inflation = 0.02

        if current_tick > 0 and current_tick % 10 == 0:
            adjustment = 0.5 * (inflation_rate - target_inflation)
            new_rate = current_rate + (adjustment * 0.1)
            new_rate = max(0.0, min(0.20, new_rate))

            if abs(new_rate - current_rate) > 0.0001:
                bank_agent.update_base_rate(new_rate)
                logger.info(
                    f"MONETARY_POLICY_UPDATE | Rate: {current_rate:.4f} -> {new_rate:.4f} (Infl: {inflation_rate:.4f})",
                    extra={"tick": current_tick, "agent_id": self.id, "tags": ["policy", "rate"]}
                )

    def invest_infrastructure(self, current_tick: int) -> bool:
        """인프라에 투자하여 전체 생산성을 향상시킵니다."""
        cost = getattr(self.config_module, "INFRASTRUCTURE_INVESTMENT_COST", 5000.0)
        
        if self.assets >= cost:
            self.assets -= cost
            self.expenditure_this_tick += cost
            self.infrastructure_level += 1
            
            logger.info(
                f"INFRASTRUCTURE_INVESTED | Level {self.infrastructure_level} reached. Cost: {cost}",
                extra={
                    "tick": current_tick,
                    "agent_id": self.id,
                    "level": self.infrastructure_level,
                    "tags": ["investment", "infrastructure"]
                }
            )
            return True
        return False

    def finalize_tick(self, current_tick: int):
        """
        Called at the end of every tick to finalize statistics and push to history buffers.
        """
        # 1. Archive Tax Revenue
        revenue_snapshot = self.current_tick_stats["tax_revenue"].copy()
        revenue_snapshot["tick"] = current_tick
        revenue_snapshot["total"] = self.current_tick_stats["total_collected"]

        self.tax_history.append(revenue_snapshot)
        if len(self.tax_history) > self.history_window_size:
            self.tax_history.pop(0)

        # 2. Archive Welfare Spending
        welfare_snapshot = {
            "tick": current_tick,
            "welfare": self.current_tick_stats["welfare_spending"],
            "stimulus": self.current_tick_stats["stimulus_spending"]
        }
        self.welfare_history.append(welfare_snapshot)
        if len(self.welfare_history) > self.history_window_size:
            self.welfare_history.pop(0)

        # 3. Reset Current Tick Stats
        self.current_tick_stats = {
            "tax_revenue": {},
            "welfare_spending": 0.0,
            "stimulus_spending": 0.0,
            "total_collected": 0.0
        }

    def get_agent_data(self) -> Dict[str, Any]:
        """정부 상태 데이터를 반환합니다."""
        return {
            "id": self.id,
            "agent_type": "government",
            "assets": self.assets,
            "total_collected_tax": self.total_collected_tax,
            "total_spent_subsidies": self.total_spent_subsidies,
            "infrastructure_level": self.infrastructure_level,
            "approval_rating": getattr(self, "approval_rating", 0.5),
            "income_tax_rate": self.income_tax_rate
        }
