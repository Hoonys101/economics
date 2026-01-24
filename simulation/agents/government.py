import logging
from typing import Dict, List, Any, Deque, Tuple
from collections import deque
from simulation.ai.enums import PoliticalParty
from simulation.interfaces.policy_interface import IGovernmentPolicy
from simulation.policies.taylor_rule_policy import TaylorRulePolicy
from simulation.policies.smart_leviathan_policy import SmartLeviathanPolicy
from simulation.dtos import GovernmentStateDTO
from typing import Optional, TYPE_CHECKING
from simulation.utils.shadow_logger import log_shadow
from simulation.models import Transaction

if TYPE_CHECKING:
    from simulation.finance.api import ISettlementSystem
    from modules.finance.api import BailoutLoanDTO
from simulation.systems.tax_agency import TaxAgency
from simulation.systems.ministry_of_education import MinistryOfEducation
from modules.finance.api import InsufficientFundsError

logger = logging.getLogger(__name__)

class Government:
    """
    정부 에이전트. 세금을 징수하고 보조금을 지급하거나 인프라에 투자합니다.
    """

    def __init__(self, id: int, initial_assets: float = 0.0, config_module: Any = None):
        self.id = id
        self._assets = initial_assets
        self.config_module = config_module
        self.settlement_system: Optional["ISettlementSystem"] = None
        
        self.tax_agency = TaxAgency(config_module)
        self.ministry_of_education = MinistryOfEducation(config_module)

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
        self.finance_system = None

        logger.info(
            f"Government {self.id} initialized with assets: {self.assets}",
            extra={"tick": 0, "agent_id": self.id, "tags": ["init", "government"]},
        )

    @property
    def assets(self) -> float:
        return self._assets

    def _add_assets(self, amount: float) -> None:
        """
        [INTERNAL ONLY] Increase assets.
        See BaseAgent._add_assets docstring.
        """
        self._assets += amount

    def _sub_assets(self, amount: float) -> None:
        """
        [INTERNAL ONLY] Decrease assets.
        See BaseAgent._sub_assets docstring.
        """
        self._assets -= amount

    def update_sensory_data(self, dto: GovernmentStateDTO):
        """
        WO-057-B: Sensory Module Interface.
        Receives 10-tick SMA macro data from the Engine.
        """
        self.sensory_data = dto
        # Log reception (Debug)
        if dto.tick % 50 == 0:
            inf_sma = dto.inflation_sma if isinstance(dto.inflation_sma, (int, float)) else 0.0
            app_sma = dto.approval_sma if isinstance(dto.approval_sma, (int, float)) else 0.0
            logger.debug(
                f"SENSORY_UPDATE | Government received macro data. Inflation_SMA: {inf_sma:.4f}, Approval_SMA: {app_sma:.2f}",
                extra={"tick": dto.tick, "agent_id": self.id, "tags": ["sensory", "wo-057-b"]}
            )

    def calculate_income_tax(self, income: float, survival_cost: float) -> float:
        """Delegates income tax calculation to the TaxAgency."""
        tax_mode = getattr(self.config_module, "TAX_MODE", "PROGRESSIVE")
        return self.tax_agency.calculate_income_tax(income, survival_cost, self.income_tax_rate, tax_mode)

    def calculate_corporate_tax(self, profit: float) -> float:
        """Delegates corporate tax calculation to the TaxAgency."""
        return self.tax_agency.calculate_corporate_tax(profit, self.corporate_tax_rate)

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

    def collect_tax(self, amount: float, tax_type: str, payer: Any, current_tick: int):
        """세금을 징수합니다."""
        # Legacy method support if any direct calls remain, though TickScheduler uses transactions now.
        return self.tax_agency.collect_tax(self, amount, tax_type, payer, current_tick)

    def record_revenue(
        self, amount: float, tax_type: str, payer_id: Any, current_tick: int
    ):
        """
        Records revenue statistics WITHOUT attempting collection (No Asset Modification).
        Used when funds are transferred via SettlementSystem manually.
        """
        self.tax_agency.record_revenue(self, amount, tax_type, payer_id, current_tick)

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

        if len(self.public_opinion_queue) > 0:
            self.perceived_public_opinion = self.public_opinion_queue[0]

        self.approval_rating = avg_approval

    def check_election(self, current_tick: int):
        """
        Checks for election cycle and handles regime change.
        """
        election_cycle = 100
        if current_tick > 0 and current_tick % election_cycle == 0:
            self.last_election_tick = current_tick

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

    def make_policy_decision(self, market_data: Dict[str, Any], current_tick: int, central_bank: "CentralBank"):
        """
        정책 엔진에게 의사결정을 위임하고 결과를 반영합니다.
        (전략 패턴 적용: Taylor Rule 또는 AI Adaptive)
        """
        # 1. 정책 엔진 실행 (Actuator 및 Shadow Mode 로직 포함)
        decision = self.policy_engine.decide(self, self.sensory_data, current_tick, central_bank)
        
        if decision.get("status") == "EXECUTED":
             logger.debug(
                f"POLICY_EXECUTED | Tick: {current_tick} | Action: {decision.get('action_taken')}",
                extra={"tick": current_tick, "agent_id": self.id}
            )

        gdp_gap = 0.0
        if self.potential_gdp > 0:
            current_gdp = market_data.get("total_production", 0.0)
            gdp_gap = (current_gdp - self.potential_gdp) / self.potential_gdp

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

        target_inflation = getattr(self.config_module, "CB_INFLATION_TARGET", 0.02)
        neutral_rate = max(0.01, real_gdp_growth)
        target_rate = neutral_rate + inflation + 0.5 * (inflation - target_inflation) + 0.5 * gdp_gap

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

    def provide_household_support(self, household: Any, amount: float, current_tick: int) -> List[Transaction]:
        """Provides subsidies to households (e.g., unemployment, stimulus). Returns transactions."""
        transactions = []
        effective_amount = amount * self.welfare_budget_multiplier

        if effective_amount <= 0:
            return []

        # Check budget, issue bonds if needed (Optimistic check)

        if self.assets < effective_amount:
            needed = effective_amount - self.assets
            # FinanceSystem now returns (bonds, transactions)
            bonds, txs = self.finance_system.issue_treasury_bonds(needed, current_tick)
            if not bonds:
                logger.warning(f"BOND_ISSUANCE_FAILED | Failed to raise {needed:.2f} for household support.")
                return []
            transactions.extend(txs)

        # Generate Welfare Transaction
        tx = Transaction(
            buyer_id=self.id,
            seller_id=household.id,
            item_id="welfare_support",
            quantity=1.0,
            price=effective_amount,
            market_id="system",
            transaction_type="welfare",
            time=current_tick
        )
        transactions.append(tx)

        self.total_spent_subsidies += effective_amount
        self.expenditure_this_tick += effective_amount
        self.current_tick_stats["welfare_spending"] += effective_amount

        logger.info(
            f"HOUSEHOLD_SUPPORT | Generated support tx of {effective_amount:.2f} to {household.id}",
            extra={"tick": current_tick, "agent_id": self.id, "amount": effective_amount, "target_id": household.id}
        )
        return transactions

    def provide_firm_bailout(self, firm: Any, amount: float, current_tick: int) -> Tuple[Optional["BailoutLoanDTO"], List[Transaction]]:
        """Provides a bailout loan to a firm if it's eligible. Returns (LoanDTO, Transactions)."""
        if self.finance_system.evaluate_solvency(firm, current_tick):
            logger.info(f"BAILOUT_APPROVED | Firm {firm.id} is eligible for a bailout.")
            # FinanceSystem now returns (loan, transactions)
            loan, txs = self.finance_system.grant_bailout_loan(firm, amount, current_tick)
            if loan:
                self.expenditure_this_tick += amount
            return loan, txs
        else:
            logger.warning(f"BAILOUT_DENIED | Firm {firm.id} is insolvent and not eligible for a bailout.")
            return None, []

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

    def run_welfare_check(self, agents: List[Any], market_data: Dict[str, Any], current_tick: int) -> List[Transaction]:
        """
        Government Main Loop Step.
        Returns List of Transactions.
        """
        transactions = []
        self.reset_tick_flow()

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
                if net_worth > wealth_threshold:
                    tax_amount = (net_worth - wealth_threshold) * wealth_tax_rate_tick
                    tax_amount = min(tax_amount, agent.assets)

                    if tax_amount > 0:
                        # Generate Tax Transaction
                        tx = Transaction(
                            buyer_id=agent.id,
                            seller_id=self.id,
                            item_id="wealth_tax",
                            quantity=1.0,
                            price=tax_amount,
                            market_id="system",
                            transaction_type="tax",
                            time=current_tick
                        )
                        transactions.append(tx)
                        total_wealth_tax += tax_amount

                # B. Unemployment Benefit
                if not agent.is_employed:
                    txs = self.provide_household_support(agent, benefit_amount, current_tick)
                    transactions.extend(txs)
                    total_welfare_paid += benefit_amount

        # 3. Stimulus Check
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
                 txs = self.provide_household_support(h, stimulus_amount, current_tick)
                 transactions.extend(txs)

                 # Calculate total from txs for logging?
                 # Assuming 1 welfare tx per support call
                 for tx in txs:
                     if tx.transaction_type == 'welfare':
                         total_stimulus += tx.price

             if total_stimulus > 0:
                 logger.warning(
                     f"STIMULUS_TRIGGERED | GDP Drop Detected. Generated stimulus txs total {total_stimulus:.2f}.",
                     extra={"tick": current_tick, "agent_id": self.id, "gdp_current": current_gdp}
                 )

        return transactions

    def invest_infrastructure(self, current_tick: int, reflux_system: Any = None) -> Tuple[bool, List[Transaction]]:
        """인프라에 투자하여 전체 생산성을 향상시킵니다. Returns (Success, Transactions)."""
        transactions = []
        cost = getattr(self.config_module, "INFRASTRUCTURE_INVESTMENT_COST", 5000.0)
        
        effective_cost = cost

        if self.firm_subsidy_budget_multiplier < 0.8:
            return False, []

        # Optimistic Check: Do we have enough + potential bond revenue?
        # Note: Since bond transactions are returned and executed later, self.assets isn't updated yet.
        # But we also delay infrastructure spending via Transaction.
        # So we check: Current Assets + (Bond Revenue) >= Cost

        potential_revenue = 0.0
        if self.assets < effective_cost:
            needed = effective_cost - self.assets
            bonds, txs = self.finance_system.issue_treasury_bonds(needed, current_tick)
            if not bonds:
                logger.warning(f"BOND_ISSUANCE_FAILED | Failed to raise {needed:.2f} for infrastructure.")
                return False, []
            transactions.extend(txs)
            potential_revenue = needed # Assume success

        # WO-Fix: Bypass TransactionProcessor for internal transfers to prevent zero-sum drift (phantom tax/leaks)
        # We execute the transfer directly using SettlementSystem if available.
        transfer_success = False

        if self.settlement_system and reflux_system:
             transfer_success = self.settlement_system.transfer(
                 self,
                 reflux_system,
                 effective_cost,
                 "Infrastructure Investment (Direct)"
             )
             if not transfer_success:
                 logger.error(f"INFRASTRUCTURE_FAIL | Settlement transfer failed.")
                 return False, []
        else:
            # Legacy Fallback (Transaction-based)
            reflux_id = 999999
            if reflux_system and hasattr(reflux_system, 'id'):
                reflux_id = reflux_system.id

            tx = Transaction(
                buyer_id=self.id, # Government Pays
                seller_id=reflux_id, # Reflux Receives
                item_id="infrastructure_investment",
                quantity=1.0,
                price=effective_cost,
                market_id="system",
                transaction_type="infrastructure",
                time=current_tick
            )
            transactions.append(tx)
            transfer_success = True # Assumed deferred success

        self.expenditure_this_tick += effective_cost
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
        return True, transactions

    def finalize_tick(self, current_tick: int):
        """
        Called at the end of every tick to finalize statistics and push to history buffers.
        """
        revenue_snapshot = self.current_tick_stats["tax_revenue"].copy()
        revenue_snapshot["tick"] = current_tick
        revenue_snapshot["total"] = self.current_tick_stats["total_collected"]

        # WO-057 Deficit Spending: Update total_debt based on FinanceSystem
        if self.finance_system:
             self.total_debt = sum(b.face_value for b in self.finance_system.outstanding_bonds)
        elif self.assets < 0:
             self.total_debt = abs(self.assets)
        else:
             self.total_debt = 0.0

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

    def get_debt_to_gdp_ratio(self) -> float:
        """Calculates the debt-to-GDP ratio."""
        if not self.sensory_data or self.sensory_data.current_gdp == 0:
            return 0.0

        debt = max(0.0, -self.assets)
        return debt / self.sensory_data.current_gdp

    def deposit(self, amount: float) -> None:
        """Deposits a given amount into the government's assets."""
        if amount > 0:
            self._assets += amount

    def withdraw(self, amount: float) -> None:
        """Withdraws a given amount from the government's assets."""
        if amount > 0:
            if self.assets < amount:
                raise InsufficientFundsError(f"Government {self.id} has insufficient funds for withdrawal of {amount:.2f}. Available: {self.assets:.2f}")
            self._assets -= amount

    # WO-054: Public Education System
    def run_public_education(self, agents: List[Any], config_module: Any, current_tick: int, reflux_system: Any = None) -> None:
        """
        Delegates public education logic to the Ministry of Education.
        """
        households = [a for a in agents if hasattr(a, 'education_level')]
        self.ministry_of_education.run_public_education(households, self, current_tick, reflux_system, self.settlement_system)
