import logging
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

        # 성향 및 욕구 (AI 훈련용 더미)
        self.value_orientation = "public_service"
        self.needs: Dict[str, float] = {}

        # GDP Tracking for Stimulus
        self.gdp_history: List[float] = [] # Stores total_production per tick
        self.gdp_history_window = 20 # 2 quarters (approx 20 ticks based on spec saying 2 quarters)
        # Note: Spec says "2분기 연속 하락". If 1 year = 100 ticks, 1 quarter = 25 ticks.
        # Let's keep a history buffer to calculate trends.

        logger.info(
            f"Government {self.id} initialized with assets: {self.assets}",
            extra={"tick": 0, "agent_id": self.id, "tags": ["init", "government"]},
        )

    def calculate_income_tax(self, income: float, survival_cost: float) -> float:
        """
        Calculates income tax based on TAX_MODE (FLAT or PROGRESSIVE).
        """
        tax_mode = getattr(self.config_module, "TAX_MODE", "PROGRESSIVE")

        if tax_mode == "FLAT":
            base_rate = getattr(self.config_module, "BASE_INCOME_TAX_RATE", 0.2)
            return income * base_rate

        # Progressive Logic
        tax_brackets = getattr(self.config_module, "TAX_BRACKETS", [])
        if not tax_brackets:
            # Fallback to flat rate if no brackets defined
            rate = getattr(self.config_module, "INCOME_TAX_RATE", 0.1)
            return income * rate

        # Brackets are defined as (multiple_of_survival_cost, rate)
        # However, for simple V1 implementation per spec:
        # "단순하게 Transaction Amount 자체에 브라켓을 적용합니다"
        # We need to find which bracket the income falls into.
        # But wait, progressive tax usually applies to chunks.
        # Spec says: "소득 구간(Tax Brackets)별 차등 세율 적용"
        # BUT Spec Clarification says: "단순하게 Transaction Amount 자체에 브라켓을 적용합니다. (V1 Simplicity)"
        # This implies a flat rate based on the total amount's bracket, OR a simplified bracket logic.
        # Let's assume standard marginal tax brackets for correctness, as "Progressive" implies that.
        # But if "V1 Simplicity" means finding the rate for the total amount and applying it to the whole, that's easier.
        # Let's read the brackets: [(1.5, 0.0), (5.0, 0.15), (inf, 0.40)]
        # This looks like: Income up to 1.5*SC is 0%. Income between 1.5*SC and 5.0*SC is 15%. Above is 40%.

        tax_total = 0.0
        remaining_income = income
        previous_limit_abs = 0.0

        for multiple, rate in tax_brackets:
            limit_abs = multiple * survival_cost

            taxable_in_this_bracket = min(max(0, limit_abs - previous_limit_abs), remaining_income)

            # If remaining_income is greater than the width of this bracket, we tax the full width
            # If remaining_income is less, we tax the remainder
            # Actually, let's do it cleanly:

            # Range for this bracket: [previous_limit_abs, limit_abs]
            # Income overlapping with this range:
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
        (실제로는 History 저장은 Tick 끝에 하는 것이 좋지만,
         Engine 흐름상 매 틱 Start 시점에 지난 틱 데이터를 Flush 하는 방식으로 처리합니다.
         단, 첫 호출시에는 0이 들어갈 수 있음)
        """
        # 현재 누적된 Flow가 있다면 History에 추가 (지난 틱 데이터)
        # 세부 Breakdown History를 위해 현재 tax_revenue와 이전 tax_revenue의 차이를 구하거나
        # 별도의 'revenue_breakdown_this_tick'을 관리해야 함.
        # 간단하게 구현하기 위해 tax_revenue_history에는 '이번 틱에 걷힌 세금 Breakdown'을 저장해야 함.
        # 하지만 collect_tax에서 전역 tax_revenue만 누적하고 있음.
        # 따라서 collect_tax에서 별도의 breakdown_this_tick 딕셔너리를 업데이트하도록 변경 필요.
        # 여기서는 buffer를 flush.

        # NOTE: collect_tax logic update needed to support breakdown history properly.
        # See collect_tax implementation below.

        if getattr(self, "revenue_breakdown_this_tick", None) is None:
             self.revenue_breakdown_this_tick = {}

        # Legacy history appending removed in favor of finalize_tick logic

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
            # 예산 부족 시 보유 자산만큼만 지급하거나 지급하지 않음
            amount = max(0.0, self.assets)
            
        if amount <= 0:
            return 0.0
            
        self.assets -= amount
        self.total_spent_subsidies += amount
        self.expenditure_this_tick += amount

        target_agent.assets += amount
        
        # Track spending type (Stimulus check is usually large lump sum, benefit is small)
        # But here we don't have explicit type.
        # run_welfare_check calls this for "benefit" and "stimulus".
        # We need to distinguish or just lump them.
        # For now, we will track total in current_tick_stats and distinguish in the caller if needed.
        # Ideally provide_subsidy should take a 'reason'.
        # Assuming run_welfare_check updates 'current_tick_stats' for type differentiation or we update here if we change signature.
        # But changing signature breaks compatibility with potential tests.
        # Let's just track total here, and let run_welfare_check add to specific buckets.
        # Actually, run_welfare_check does not update buckets.
        # Let's update `current_tick_stats["welfare_spending"]` here.

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

    def run_welfare_check(self, agents: List[Any], market_data: Dict[str, Any], current_tick: int):
        """
        Phase 4: Performs welfare checks, wealth tax collection, and stimulus injection.
        Called every tick by the Engine.
        """
        # 1. Calculate Survival Cost (Dynamic)
        # max(avg_food_price * daily_food_need, 10.0)
        avg_food_price = 0.0
        goods_market = market_data.get("goods_market", {})
        if "basic_food_current_sell_price" in goods_market:
            avg_food_price = goods_market["basic_food_current_sell_price"]
        else:
            avg_food_price = getattr(self.config_module, "GOODS_INITIAL_PRICE", {}).get("basic_food", 5.0)

        # Assuming FOOD_CONSUMPTION_MAX_PER_TICK or similar as daily need.
        # Config says HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0.
        # Let's use HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK if available.
        daily_food_need = getattr(self.config_module, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 1.0)

        survival_cost = max(avg_food_price * daily_food_need, 10.0)

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

            # We only tax/support Households (checking agent_type or class would be better but duck typing works)
            if hasattr(agent, "needs") and hasattr(agent, "is_employed"): # Identifying Household

                # A. Wealth Tax
                net_worth = agent.assets # Simplified Net Worth (ignoring debts/stocks value for now for speed, or assume assets includes cash)
                # Ideally Net Worth = Cash + Stock Value - Debt.
                # agent.assets is usually just Cash.
                # Let's use Cash + Stock Value if possible, but spec says "Net Assets".
                # For Phase 4 V1, let's stick to Cash or see if we can easily get Stock Value.
                # agent.shares_owned exists. We need stock prices.
                # Computing full net worth might be expensive inside this loop if we do lookup.
                # Let's stick to agent.assets (Cash) for now unless spec demands rigorous Net Worth.
                # Spec says "Net Assets (Net Worth)".
                # Let's try to add stock value if market_data has it.
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
                        # Asset poor but stock rich? Force sell?
                        # For now, just take what cash is available.
                        taken = agent.assets
                        agent.assets = 0
                        self.collect_tax(taken, "wealth_tax", agent.id, current_tick)
                        total_wealth_tax += taken

                # B. Unemployment Benefit
                # Spec: is_employed = False AND looking_for_work = True
                # "looking_for_work" isn't explicitly tracked as a flag in Household,
                # but unemployed households generally look for work.
                if not agent.is_employed:
                    # Provide benefit
                    # Check Government budget? Spec says "Treasury. If deficient, Money Printing".
                    # So we always pay.
                    if self.assets < benefit_amount:
                        # Deficit Spending / Money Printing
                        self.assets += benefit_amount # Print money
                        logger.info(f"DEFICIT_SPENDING | Government printed {benefit_amount:.2f} for welfare.", extra={"tick": current_tick, "agent_id": self.id})

                    self.provide_subsidy(agent, benefit_amount, current_tick)
                    total_welfare_paid += benefit_amount

        # 3. Stimulus Check (Helicopter Money)
        # Condition: GDP drops significantly.
        # Check Tracker for total_production?
        # The Engine calls this method. We should have access to GDP via market_data or passed args.
        # market_data usually contains price info. GDP (Total Production) is in Tracker.
        # But we need history.
        # Let's rely on the Engine to pass the latest GDP or we fetch it if we had access to tracker.
        # Currently run_welfare_check signature is (agents, market_data, current_tick).
        # We might need to track GDP history internally in Government class by having Engine pass current GDP.

        # NOTE: Engine should pass `current_gdp` to this method.
        # I will update the signature in the next step or assume it is in market_data if I put it there.
        # Let's check `market_data` usage in Engine. It has "goods_market", "stock_market".
        # I'll rely on a new argument `current_gdp` or extract from `market_data` if I hack it in.
        # Better: Add `current_gdp` to `run_welfare_check` signature.
        # For now, I'll access it from `market_data` assuming I add it there in Engine.

        current_gdp = market_data.get("total_production", 0.0)
        self.gdp_history.append(current_gdp)
        if len(self.gdp_history) > self.gdp_history_window:
            self.gdp_history.pop(0)

        # Trigger Logic: "2분기 연속 하락" (Falling for 2 quarters)
        # Simplified: Check if average of last quarter < average of quarter before that?
        # Or checking a "drop" threshold defined in config.
        # Spec: "GDP 5% drop trigger" (STIMULUS_TRIGGER_GDP_DROP = -0.05)
        # Let's compare current GDP vs GDP 10 ticks ago (approx short term trend).
        trigger_drop = getattr(self.config_module, "STIMULUS_TRIGGER_GDP_DROP", -0.05)

        should_stimulus = False
        if len(self.gdp_history) >= 10:
            past_gdp = self.gdp_history[-10]
            if past_gdp > 0:
                change = (current_gdp - past_gdp) / past_gdp
                if change <= trigger_drop:
                    should_stimulus = True

        if should_stimulus:
             stimulus_amount = survival_cost * 5.0 # Example lump sum
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
             # Reset history or cooldown to prevent continuous stimulus?
             # Spec doesn't say. Let's add a cooldown implicit by the fact that GDP needs to drop AGAIN to trigger.
             # But if it stays low, the comparison might stabilize.
             # If it keeps dropping, we keep paying. This seems correct for "Rescue".

    def update_monetary_policy(self, bank_agent: Any, current_tick: int, inflation_rate: float = 0.0):
        """
        중앙은행 역할: 인플레이션 등에 따라 기준 금리를 조절합니다.
        (현재는 간단한 Rule-based 로직: 인플레가 높으면 금리 인상)
        """
        # Phase 3: Start of Tick Logic for Government (Reset Flow)
        self.reset_tick_flow()

        # 기본 금리 가져오기
        current_rate = bank_agent.base_rate

        # 목표 인플레이션 (예: 2%)
        target_inflation = 0.02

        # Taylor Rule Simplified
        # Rate = Current + 0.5 * (Inflation - Target)
        # 틱당 호출되므로 변화폭을 매우 작게 하거나, 분기별로 호출해야 함.
        # 여기서는 매 틱 아주 미세하게 조정하거나, 특정 주기에만 조정.

        if current_tick > 0 and current_tick % 10 == 0: # 10틱마다 조정
            adjustment = 0.5 * (inflation_rate - target_inflation)
            # 스무딩
            new_rate = current_rate + (adjustment * 0.1)

            # 하한/상한 (0% ~ 20%)
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
            "infrastructure_level": self.infrastructure_level
        }
