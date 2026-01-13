import logging
from typing import Dict, List, Any, Deque
from collections import deque
from simulation.ai.enums import PoliticalParty
from simulation.interfaces.policy_interface import IGovernmentPolicy
from simulation.policies.taylor_rule_policy import TaylorRulePolicy
from simulation.policies.smart_leviathan_policy import SmartLeviathanPolicy
from simulation.dtos import GovernmentStateDTO
from typing import Optional
from simulation.utils.shadow_logger import log_shadow

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

        # Gold Standard Money Tracking
        self.total_money_issued: float = 0.0
        self.total_money_destroyed: float = 0.0
        
        # 세수 유형별 집계
        self.tax_revenue: Dict[str, float] = {}

        # --- Phase 7: Adaptive Fiscal Policy State ---
        self.potential_gdp: float = 0.0
        self.gdp_ema: float = 0.0
        self.fiscal_stance: float = 0.0

        # --- Phase 24: Policy Strategy Selection ---
        policy_mode = getattr(config_module, "GOVERNMENT_POLICY_MODE", "TAYLOR_RULE")
        if policy_mode == "AI_ADAPTIVE":
            self.policy_engine: IGovernmentPolicy = SmartLeviathanPolicy(self, config_module)
        else:
            self.policy_engine: IGovernmentPolicy = TaylorRulePolicy(config_module)

        # Legacy / Compatibility
        self.ai = getattr(self.policy_engine, "ai", None)

        # Political State
        self.ruling_party: PoliticalParty = PoliticalParty.BLUE # Default
        self.approval_rating: float = 0.5
        self.public_opinion_queue: Deque[float] = deque(maxlen=4) # 4-tick lag
        self.perceived_public_opinion: float = 0.5
        self.last_election_tick: int = 0

        # Policy Levers (Tax Rates)
        self.income_tax_rate: float = getattr(config_module, "INCOME_TAX_RATE", 0.1)
        self.corporate_tax_rate: float = getattr(config_module, "CORPORATE_TAX_RATE", 0.2)

        # Spending Multipliers (AI Controlled)
        # 1.0 = Normal (Budget Neutral-ish), >1.0 = Stimulus, <1.0 = Austerity
        self.welfare_budget_multiplier: float = 1.0
        self.firm_subsidy_budget_multiplier: float = 1.0

        self.effective_tax_rate: float = self.income_tax_rate # Legacy compatibility
        self.total_debt: float = 0.0
        # ---------------------------------------------

        # History buffers for visualization
        self.tax_history: List[Dict[str, Any]] = [] # For Stacked Bar Chart (breakdown per tick)
        self.welfare_history: List[Dict[str, float]] = [] # For Welfare Line Chart
        self.history_window_size = 5000

        # Current tick accumulators (reset every tick)
        self.current_tick_stats = {
            "tax_revenue": {},
            "welfare_spending": 0.0,
            "stimulus_spending": 0.0,
            "total_collected": 0.0,
            "education_spending": 0.0 # WO-054
        }

        # GDP Tracking for Stimulus
        self.gdp_history: List[float] = []
        self.gdp_history_window = 20
        
        # WO-056: Shadow Policy Metrics
        ticks_per_year = int(getattr(config_module, "TICKS_PER_YEAR", 100))
        self.price_history_shadow: Deque[float] = deque(maxlen=ticks_per_year)

        self.revenue_this_tick = 0.0
        self.expenditure_this_tick = 0.0
        self.revenue_breakdown_this_tick = {}
        
        self.average_approval_rating = 0.5

        # WO-057-B: Sensory Data Container
        self.sensory_data: Optional[GovernmentStateDTO] = None

        logger.info(
            f"Government {self.id} initialized with assets: {self.assets}",
            extra={"tick": 0, "agent_id": self.id, "tags": ["init", "government"]},
        )

    def update_sensory_data(self, dto: GovernmentStateDTO):
        """
        WO-057-B: Sensory Module Interface.
        Receives 10-tick SMA macro data from the Engine.
        """
        self.sensory_data = dto
        # Log reception (Debug)
        if dto.tick % 50 == 0:
            logger.debug(
                f"SENSORY_UPDATE | Government received macro data. Inflation_SMA: {dto.inflation_sma:.4f}, Approval_SMA: {dto.approval_sma:.2f}",
                extra={"tick": dto.tick, "agent_id": self.id, "tags": ["sensory", "wo-057-b"]}
            )

    def calculate_income_tax(self, income: float, survival_cost: float) -> float:
        """
        Calculates income tax based on TAX_MODE and income_tax_rate.
        """
        tax_mode = getattr(self.config_module, "TAX_MODE", "PROGRESSIVE")

        if tax_mode == "FLAT":
            return income * self.income_tax_rate

        # Progressive Logic
        tax_brackets = getattr(self.config_module, "TAX_BRACKETS", [])
        if not tax_brackets:
            return income * self.income_tax_rate

        # Calculate raw tax based on brackets
        raw_tax = 0.0
        remaining_income = income
        previous_limit_abs = 0.0

        for multiple, rate in tax_brackets:
            limit_abs = multiple * survival_cost
            upper_bound = min(income, limit_abs)
            lower_bound = max(0, previous_limit_abs)
            taxable_amount = max(0.0, upper_bound - lower_bound)

            if taxable_amount > 0:
                raw_tax += taxable_amount * rate

            if income <= limit_abs:
                break
            previous_limit_abs = limit_abs

        # Scale tax based on current income_tax_rate vs base rate in config
        # If policy lowers tax rate, we scale the bracket result down.
        base_rate_config = getattr(self.config_module, "TAX_RATE_BASE", 0.1)
        if base_rate_config > 0:
            adjustment_factor = self.income_tax_rate / base_rate_config
            return raw_tax * adjustment_factor
        else:
            return raw_tax

    def calculate_corporate_tax(self, profit: float) -> float:
        """Calculates corporate tax."""
        if profit <= 0:
            return 0.0
        return profit * self.corporate_tax_rate

    def reset_tick_flow(self):
        """
        매 틱 시작 시 호출되어 이번 틱의 Flow 데이터를 초기화하고,
        이전 틱의 데이터를 History에 저장합니다.
        """
        if getattr(self, "revenue_breakdown_this_tick", None) is None:
             self.revenue_breakdown_this_tick = {}

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

        # Money Destruction (Gold Standard / Fiat Sink)
        self.total_money_destroyed += amount
        
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

    def update_public_opinion(self, households: List[Any]):
        """
        Aggregates approval ratings from households and updates the opinion queue (Lag).
        """
        total_approval = 0
        count = 0
        for h in households:
            if h.is_active:
                # Household must have 'approval_rating' (0 or 1)
                rating = getattr(h, "approval_rating", 0)
                total_approval += rating
                count += 1

        avg_approval = total_approval / count if count > 0 else 0.5
        self.public_opinion_queue.append(avg_approval)

        # Update Perceived Opinion (Lagged)
        # We take the oldest value in the queue (FIFO)
        # If queue is full (len 4), index 0 is 4 ticks ago.
        if len(self.public_opinion_queue) > 0:
            self.perceived_public_opinion = self.public_opinion_queue[0]

        self.approval_rating = avg_approval # Real-time value (for omniscient logging)

    def check_election(self, current_tick: int):
        """
        Checks for election cycle and handles regime change.
        """
        election_cycle = 100
        if current_tick > 0 and current_tick % election_cycle == 0:
            self.last_election_tick = current_tick

            # Retrospective Voting
            # If Perceived Opinion < 0.5 (Tolerance), Incumbent loses.
            if self.perceived_public_opinion < 0.5:
                # Flip Party
                old_party = self.ruling_party
                self.ruling_party = PoliticalParty.RED if old_party == PoliticalParty.BLUE else PoliticalParty.BLUE

                logger.warning(
                    f"ELECTION_RESULTS | REGIME CHANGE! {old_party.name} -> {self.ruling_party.name}. Approval: {self.perceived_public_opinion:.2f}",
                    extra={"tick": current_tick, "agent_id": self.id, "tags": ["election", "regime_change"]}
                )
            else:
                logger.info(
                    f"ELECTION_RESULTS | INCUMBENT VICTORY ({self.ruling_party.name}). Approval: {self.perceived_public_opinion:.2f}",
                    extra={"tick": current_tick, "agent_id": self.id, "tags": ["election"]}
                )

    def make_policy_decision(self, market_data: Dict[str, Any], current_tick: int):
        """
        정책 엔진에게 의사결정을 위임하고 결과를 반영합니다.
        (전략 패턴 적용: Taylor Rule 또는 AI Adaptive)
        """
        # 1. 정책 엔진 실행 (Actuator 및 Shadow Mode 로직 포함)
        decision = self.policy_engine.decide(self, market_data, current_tick)
        
        # 2. 결과 로깅 (엔진 내부에서 상세 로깅 수행)
        if decision.get("status") == "EXECUTED":
             logger.debug(
                f"POLICY_EXECUTED | Tick: {current_tick} | Action: {decision.get('action_taken')}",
                extra={"tick": current_tick, "agent_id": self.id}
            )


        gdp_gap = 0.0
        if self.potential_gdp > 0:
            current_gdp = market_data.get("total_production", 0.0)
            gdp_gap = (current_gdp - self.potential_gdp) / self.potential_gdp

            # Simple EMA update for Potential GDP
            alpha = 0.01
            self.potential_gdp = (alpha * current_gdp) + ((1-alpha) * self.potential_gdp)

        # 1. Calculate Inflation (YoY)
        inflation = 0.0
        if len(self.price_history_shadow) >= 2:
            current_p = self.price_history_shadow[-1]
            past_p = self.price_history_shadow[0]
            if past_p > 0:
                inflation = (current_p - past_p) / past_p

        # 2. Calculate Real GDP Growth
        real_gdp_growth = 0.0
        if len(self.gdp_history) >= 2:
            current_gdp = self.gdp_history[-1]
            past_gdp = self.gdp_history[-2]
            if past_gdp > 0:
                real_gdp_growth = (current_gdp - past_gdp) / past_gdp

        # 5. Taylor Rule 2.0
        # Target_Rate = Real_GDP_Growth + Inflation + 0.5*(Inf - Target_Inf) + 0.5*(GDP_Gap)
        target_inflation = getattr(self.config_module, "CB_INFLATION_TARGET", 0.02)

        # Neutral Rate assumption: Real Growth
        neutral_rate = max(0.01, real_gdp_growth) # Floor at 1%?

        target_rate = neutral_rate + inflation + 0.5 * (inflation - target_inflation) + 0.5 * gdp_gap

        # 6. Log
        # Get current base rate from market_data["loan_market"] or similar
        current_base_rate = 0.05
        if "loan_market" in market_data:
            current_base_rate = market_data["loan_market"].get("interest_rate", 0.05)

        gap = target_rate - current_base_rate

        log_shadow(
            tick=current_tick,
            agent_id=self.id,
            agent_type="Government",
            metric="taylor_rule_rate",
            current_value=current_base_rate,
            shadow_value=target_rate,
            details=f"Inf={inflation:.2%}, Growth={real_gdp_growth:.2%}, Gap={gdp_gap:.2%}, RateGap={gap:.4f}"
        )

    def provide_subsidy(self, target_agent: Any, amount: float, current_tick: int):
        """
        보조금을 지급합니다.
        AI Spending Multiplier 적용.
        """
        # Apply Multiplier based on Target
        effective_amount = amount
        agent_type = "household"
        if hasattr(target_agent, "employees"): # Duck typing Firm
            effective_amount *= self.firm_subsidy_budget_multiplier
            agent_type = "firm"
        else:
            effective_amount *= self.welfare_budget_multiplier

        if effective_amount <= 0:
            return 0.0

        if not getattr(self.config_module, "GOVERNMENT_STIMULUS_ENABLED", True):
            return 0.0

        if self.assets < effective_amount:
            # Partial payment? Or reject.
            # Logging rejection once per tick might be better to reduce noise, but let's keep logic simple.
            return 0.0

        self.assets -= effective_amount
        self.total_spent_subsidies += effective_amount
        self.expenditure_this_tick += effective_amount

        self.total_money_issued += effective_amount

        target_agent.assets += effective_amount
        self.current_tick_stats["welfare_spending"] += effective_amount

        logger.info(
            f"SUBSIDY_PAID | Paid {effective_amount:.2f} subsidy to {target_agent.id} ({agent_type})",
            extra={
                "tick": current_tick,
                "agent_id": self.id,
                "amount": effective_amount,
                "target_id": target_agent.id,
                "tags": ["subsidy", "expenditure"]
            }
        )
        return effective_amount

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
        Government Main Loop Step.
        1. Reset Tick Flow.
        2. Make AI Policy Decisions (Act).
        3. Check Election (Judge).
        4. Execute Welfare/Stimulus (using updated policy).
        """
        # Ensure tick flow is reset at the start of government processing
        self.reset_tick_flow()

        # --- Phase 17-5: Leviathan Logic ---
        # 1. Update Opinion & Make Decision
        # Note: Opinion is updated by Engine calling update_public_opinion BEFORE this method?
        # Yes, Plan says engine.py loop will call update_public_opinion -> make_decision -> check_election.
        # But here in run_welfare_check, we can group them if engine calls this.
        # Current engine.py calls run_welfare_check.
        # So I will move the AI calls HERE or keep them in Engine.
        # The prompt plan says "Update Simulation Engine... Call household.update_political_opinion... government.update_public_opinion... make_policy_decision".
        # If I put them in Engine, run_welfare_check becomes just "Execute Welfare".
        # Let's keep run_welfare_check focused on Welfare execution, and let Engine handle the high level "Government Thinking".

        # However, run_welfare_check also did "adjust_fiscal_policy".
        # I should REMOVE the old `adjust_fiscal_policy` call here as AI replaces it.
        # I removed it below.

        # ---------------------------------------

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
                # Stock Value logic skipped for brevity/speed as per original

                if net_worth > wealth_threshold:
                    tax_amount = (net_worth - wealth_threshold) * wealth_tax_rate_tick
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
                    # provide_subsidy now applies welfare_budget_multiplier
                    self.provide_subsidy(agent, benefit_amount, current_tick)
                    total_welfare_paid += benefit_amount

        # 3. Stimulus Check (Legacy Logic, now influenced by AI multiplier)
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
                 paid = self.provide_subsidy(h, stimulus_amount, current_tick)
                 total_stimulus += paid

             if total_stimulus > 0:
                 logger.warning(
                     f"STIMULUS_TRIGGERED | GDP Drop Detected. Paid {total_stimulus:.2f}.",
                     extra={"tick": current_tick, "agent_id": self.id, "gdp_current": current_gdp}
                 )

    def invest_infrastructure(self, current_tick: int, reflux_system: Any = None) -> bool:
        """인프라에 투자하여 전체 생산성을 향상시킵니다."""
        cost = getattr(self.config_module, "INFRASTRUCTURE_INVESTMENT_COST", 5000.0)
        
        # Apply AI Multiplier? Maybe firm subsidy multiplier applies here too?
        # Let's say BLUE party loves infrastructure.
        effective_cost = cost # Cost is fixed, but decision to buy depends on funds

        # If multiplier < 1.0 (Austerity), maybe we skip investment?
        if self.firm_subsidy_budget_multiplier < 0.8:
            return False

        if self.assets >= effective_cost:
            self.assets -= effective_cost
            self.total_money_issued += effective_cost # Correct money supply accounting
            self.expenditure_this_tick += effective_cost
            if reflux_system:
                reflux_system.capture(effective_cost, str(self.id), "infrastructure")

            self.infrastructure_level += 1
            
            logger.info(
                f"INFRASTRUCTURE_INVESTED | Level {self.infrastructure_level} reached. Cost: {effective_cost}",
                extra={
                    "tick": current_tick,
                    "agent_id": self.id,
                    "level": self.infrastructure_level,
                    "tags": ["investment", "infrastructure"]
                }
            )
            return True
        else:
            # Silent rejection to avoid log spam if just poor
            return False

    def finalize_tick(self, current_tick: int):
        """
        Called at the end of every tick to finalize statistics and push to history buffers.
        """
        revenue_snapshot = self.current_tick_stats["tax_revenue"].copy()
        revenue_snapshot["tick"] = current_tick
        revenue_snapshot["total"] = self.current_tick_stats["total_collected"]

        self.tax_history.append(revenue_snapshot)
        if len(self.tax_history) > self.history_window_size:
            self.tax_history.pop(0)

        welfare_snapshot = {
            "tick": current_tick,
            "welfare": self.current_tick_stats["welfare_spending"],
            "stimulus": self.current_tick_stats["stimulus_spending"],
            "education": self.current_tick_stats.get("education_spending", 0.0), # WO-054
            "debt": self.total_debt,
            "assets": self.assets
        }
        self.welfare_history.append(welfare_snapshot)
        if len(self.welfare_history) > self.history_window_size:
            self.welfare_history.pop(0)

        self.current_tick_stats = {
            "tax_revenue": {},
            "welfare_spending": 0.0,
            "stimulus_spending": 0.0,
            "education_spending": 0.0, # WO-054
            "total_collected": 0.0
        }

    def get_monetary_delta(self) -> float:
        return self.total_money_issued - self.total_money_destroyed

    def get_agent_data(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_type": "government",
            "assets": self.assets,
            "ruling_party": self.ruling_party.name,
            "approval_rating": self.approval_rating,
            "income_tax_rate": self.income_tax_rate,
            "corporate_tax_rate": self.corporate_tax_rate,
            "perceived_public_opinion": self.perceived_public_opinion
        }

    # WO-054: Public Education System
    def run_public_education(self, agents: List[Any], config_module: Any, current_tick: int, reflux_system: Any = None) -> None:
        """
        WO-054: Public Education System Implementation.
        1. Free Basic Education (Level 0 -> 1)
        2. Meritocratic Scholarship (Top Talent + Low Wealth)
        """
        budget_ratio = getattr(config_module, "PUBLIC_EDU_BUDGET_RATIO", 0.20)
        edu_budget = self.assets * budget_ratio
        spent_total = 0.0

        # Sort agents by wealth to identify scholarship candidates (Bottom 20%)
        active_households = [a for a in agents if getattr(a, "is_active", False) and a.__class__.__name__ == "Household"]
        if not active_households:
            return

        active_households.sort(key=lambda x: x.assets)
        cutoff_idx = int(len(active_households) * getattr(config_module, "SCHOLARSHIP_WEALTH_PERCENTILE", 0.20))
        # Poor households set
        poor_households = set(h.id for h in active_households[:cutoff_idx])

        # Cost map
        costs = getattr(config_module, "EDUCATION_COST_PER_LEVEL", {1: 500})
        scholarship_potential_threshold = getattr(config_module, "SCHOLARSHIP_POTENTIAL_THRESHOLD", 0.7)

        for agent in active_households:
            current_level = getattr(agent, "education_level", 0)
            next_level = current_level + 1
            cost = costs.get(next_level, 100000.0) # High default if not in map

            # 1. Free Basic Education (0 -> 1)
            if current_level == 0:
                if edu_budget >= cost:
                    agent.education_level = 1
                    edu_budget -= cost
                    self.assets -= cost
                    spent_total += cost

                    # Log event
                    logger.debug(
                        f"EDU_BASIC_GRANT | Household {agent.id} promoted to Level 1. Cost: {cost}",
                        extra={"tick": current_tick, "agent_id": self.id, "target_id": agent.id}
                    )

            # 2. Meritocratic Scholarship (Level 1+)
            elif current_level >= 1:
                # Eligibility: Poor AND High Aptitude
                is_poor = agent.id in poor_households
                has_potential = getattr(agent, "aptitude", 0.0) >= scholarship_potential_threshold

                if is_poor and has_potential:
                    subsidy = cost * 0.8 # 80% subsidy
                    student_share = cost * 0.2

                    if edu_budget >= subsidy and agent.assets >= student_share:
                        agent.education_level = next_level
                        # Pay subsidy
                        edu_budget -= subsidy
                        self.assets -= subsidy
                        spent_total += subsidy

                        # Student pays share
                        agent.assets -= student_share
                        if reflux_system:
                            reflux_system.capture(student_share, f"Household_{agent.id}", "education_tuition")

                        logger.info(
                            f"EDU_SCHOLARSHIP | Household {agent.id} (Aptitude {agent.aptitude:.2f}) promoted to Level {next_level}. Subsidy: {subsidy:.2f}, Student Share: {student_share:.2f}",
                            extra={"tick": current_tick, "agent_id": self.id, "target_id": agent.id, "aptitude": agent.aptitude}
                        )

        self.expenditure_this_tick += spent_total
        self.total_money_issued += spent_total 
        if reflux_system:
            reflux_system.capture(spent_total, str(self.id), "education_services")
        # Actually education cost usually goes to "Education Service" provider if it exists.
        # But here we assume it's just state investment (sunk cost or transfer to abstraction).
        # Since Education Service exists as a generic sector, maybe we should buy it?
        # But WO-054 implies direct level up.
        # We'll treat it as expenditure.

        self.current_tick_stats["education_spending"] = spent_total
