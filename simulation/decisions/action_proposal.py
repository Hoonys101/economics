import logging
import random
from typing import Optional, Any, List
from simulation.models import Order


class ActionProposalEngine:
    """
    에이전트의 상태에 기반하여 현실적인 후보 행동(주문) 목록을 생성합니다.
    '어떤 행동들을 할 수 있는가?'에 대한 책임을 집니다.
    """

    def __init__(
        self,
        config_module: Any,
        n_action_samples: int = 10,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.config_module = config_module
        self.n_action_samples = n_action_samples
        self.logger = (
            logger if logger else logging.getLogger(__name__)
        )  # Initialize logger

    def propose_actions(self, agent: Any, current_time: int) -> List[List[Order]]:
        """
        에이전트 유형에 따라 적절한 행동 제안 메서드를 호출합니다.
        """
        agent_type = agent.__class__.__name__.lower()
        if agent_type == "household":
            return self._propose_household_actions(agent, current_time)
        elif agent_type == "firm":
            return self._propose_firm_actions(agent, current_time)
        return []

    def _propose_household_actions(
        self, agent: Any, current_time: int
    ) -> List[List[Order]]:
        self.logger.debug(
            f"DEBUG: Entering _propose_household_actions for Household {agent.id}. Assets: {agent.assets:.2f}, is_employed: {agent.is_employed}",
            extra={
                "tick": current_time,
                "agent_id": agent.id,
                "tags": ["debug_propose_actions_entry"],
            },
        )
        """
        가계 에이전트를 위한 다양한 후보 행동들을 생성합니다.
        - 노동 시장 참여 (실직 상태이고 자산이 적을 경우)
        - 상품 시장 참여 (구매)
        """
        candidate_action_sets = []
        for _ in range(self.n_action_samples):
            orders = []
            # 행동 결정: 노동 시장 참여 또는 상품 구매
            explore_labor_market = False

            condition_assets_low = (
                agent.assets
                < self.config_module.HOUSEHOLD_ASSETS_THRESHOLD_FOR_LABOR_SUPPLY
            )
            condition_random_check = (
                random.random()
                < self.config_module.FORCED_LABOR_EXPLORATION_PROBABILITY
            )

            self.logger.debug(
                f"DEBUG: Household {agent.id} labor conditions: is_employed={agent.is_employed}, assets={agent.assets:.2f} < threshold={self.config_module.HOUSEHOLD_ASSETS_THRESHOLD_FOR_LABOR_SUPPLY} ({condition_assets_low}), random_check={condition_random_check}",
                extra={
                    "tick": current_time,
                    "agent_id": agent.id,
                    "tags": ["debug_labor_conditions"],
                },
            )

            if not agent.is_employed and condition_assets_low:
                if condition_random_check:
                    explore_labor_market = True

            if explore_labor_market or (
                not agent.is_employed and random.random() < 0.5
            ):
                self.logger.debug(
                    f"DEBUG: Household {agent.id} is attempting to sell labor. explore_labor_market: {explore_labor_market}, is_employed: {agent.is_employed}",
                    extra={
                        "tick": current_time,
                        "agent_id": agent.id,
                        "tags": ["debug_labor_sell"],
                    },
                )
                # 노동 시장에 노동력 판매 주문
                # --- Phase 21.6: The Invisible Hand (Track A: Reservation Wage) ---
                # Legacy Support: Accessing market_data via agent if available
                should_refuse = False
                if hasattr(agent, "decision_engine") and hasattr(agent.decision_engine, "context"):
                    # Only if context is persisted, which is unlikely in V1 proposal logic.
                    # Best effort: Use simple assumption or skip for legacy
                    pass

                # Check for Market Data availability (if passed or attached)
                # Assuming ActionProposal doesn't strictly enforce this check
                # but we will try to mimic if possible.

                desired_wage = (
                    self.config_module.LABOR_MARKET_MIN_WAGE * random.uniform(0.9, 1.3)
                )
                orders.append(
                    Order(agent.id, "SELL", "labor", 1, desired_wage, "labor_market")
                )
            else:
                # 상품 시장에서 상품 구매 주문
                if agent.assets > 1:  # 최소한의 자산이 있을 때만 구매 시도
                    # Read available goods from config with fallback
                    # Priority: ConfigManager.get() -> ConfigModule.HOUSEHOLD_CONSUMABLE_GOODS -> Default
                    if hasattr(self.config_module, "get"):
                        available_goods = self.config_module.get(
                            "simulation.household_consumable_goods",
                            ["basic_food", "luxury_food"],
                        )
                    else:
                        available_goods = getattr(
                            self.config_module,
                            "HOUSEHOLD_CONSUMABLE_GOODS",
                            ["basic_food", "luxury_food"]
                        )

                    good_to_trade = random.choice(available_goods)

                    # --- 개선된 구매 수량 로직 ---
                    # 자산의 일부를 지출 예산으로 설정
                    spending_ratio = random.uniform(0.05, 0.3)  # 자산의 5% ~ 30% 사용
                    budget = agent.assets * spending_ratio

                    # 인지된 가격 또는 기본 가격 사용
                    price = agent.perceived_avg_prices.get(
                        good_to_trade, self.config_module.GOODS_MARKET_SELL_PRICE
                    )
                    price = max(price, 0.01)  # 가격이 0이 되는 것 방지

                    max_quantity = budget / price

                    if max_quantity > 1:
                        # 구매 수량을 1과 최대 가능 수량 사이에서 랜덤하게 결정
                        quantity = random.uniform(1, max_quantity)
                    else:
                        # 최대 가능 수량이 1보다 작으면, 그 수량 내에서 결정
                        quantity = random.uniform(max_quantity / 2, max_quantity)

                    if quantity > 0:
                        order_price = price * random.uniform(
                            0.95, 1.15
                        )  # 가격 약간 변동시켜 제안
                        orders.append(
                            Order(
                                agent.id,
                                "BUY",
                                good_to_trade,
                                quantity,
                                order_price,
                                "goods_market",
                            )
                        )

            if orders:
                candidate_action_sets.append(orders)

        return candidate_action_sets

    def _propose_firm_actions(self, agent: Any, current_time: int) -> List[List[Order]]:
        """
        기업 에이전트를 위한 다양한 후보 행동들을 생성합니다.
        - 노동 시장 참여 (고용)
        - 상품 시장 참여 (판매)
        """
        candidate_action_sets = []
        for _ in range(self.n_action_samples):
            orders = []
            # 행동 결정: 노동력 구매 또는 상품 판매
            if random.random() < 0.5:  # TODO: 더 정교한 로직으로 변경
                # 노동 시장에 노동력 구매 주문
                offer_wage = (
                    self.config_module.INITIAL_WAGE
                    * random.uniform(0.9, 1.1)
                )
                orders.append(
                    Order(agent.id, "BUY", "labor", 1, offer_wage, "labor_market")
                )
            else:
                # 상품 시장에 상품 판매 주문
                good_to_trade = agent.specialization

                if agent.inventory.get(good_to_trade, 0) > 0:
                    price = self.config_module.GOODS_MARKET_SELL_PRICE * random.uniform(
                        0.9, 1.1
                    )
                    # 재고의 일부를 판매 수량으로 결정
                    quantity = random.uniform(
                        0.1, agent.inventory.get(good_to_trade, 0)
                    )
                    orders.append(
                        Order(
                            agent.id,
                            "SELL",
                            good_to_trade,
                            quantity,
                            price,
                            "goods_market",
                        )
                    )

            if orders:
                candidate_action_sets.append(orders)

        return candidate_action_sets

    def propose_forced_labor_action(
        self, household: Any, current_time: int, wage_factor: float
    ) -> Order:
        """
        강제 탐험을 위한 노동 판매 행동을 제안합니다.
        """
        # 희망 임금 조정 (강제 탐험 시 임금 할인)
        desired_wage = (
            self.config_module.LABOR_MARKET_MIN_WAGE
            * random.uniform(0.9, 1.3)
            * wage_factor
        )
        return Order(household.id, "SELL", "labor", 1, desired_wage, "labor_market")
