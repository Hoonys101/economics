from typing import List, Dict, Optional
import logging
from abc import ABC, abstractmethod

from simulation.models import Order, Transaction

logger = logging.getLogger(__name__)


class Market(ABC):
    """
    모든 시장의 기반이 되는 추상 클래스입니다.
    주문 접수, 매칭, 거래 기록 등 시장의 기본적인 기능을 정의합니다.

    Attributes:
        id (str): 시장의 고유 식별자입니다.
        matched_transactions (List[Transaction]): 시장에서 매칭되어 완료된 거래 기록 리스트입니다.

    Note:
        `buy_orders` and `sell_orders` attributes are implementation-specific (e.g., properties in OrderBookMarket)
        and are no longer enforced by the base class to allow for protocol compliance (TD-271).
    """

    def __init__(self, market_id: str, logger: Optional[logging.Logger] = None):
        self.id = market_id
        self.matched_transactions: List[Transaction] = []
        self.logger = logger if logger is not None else logging.getLogger(f"Market_{market_id}")

    @abstractmethod
    def place_order(self, order: Order, current_time: int) -> List[Transaction]:
        """
        주문을 시장에 접수하고 즉시 매칭을 시도합니다.
        이 메서드는 하위 클래스에서 반드시 구현되어야 합니다.

        Args:
            order (Order): 시장에 제출될 주문 객체입니다.
            current_time (int): 현재 시뮬레이션 틱 (시간) 입니다.

        Returns:
            List[Transaction]: 주문 매칭 결과로 생성된 거래(Transaction) 객체들의 리스트입니다.
                              매칭된 거래가 없으면 빈 리스트를 반환합니다.
        """
        raise NotImplementedError

    @abstractmethod
    def match_orders(self, current_time: int) -> List[Transaction]:
        """
        현재 시장에 제출된 매수/매도 주문들을 매칭하여 거래를 생성합니다.
        이 메서드는 하위 클래스에서 반드시 구현되어야 합니다.

        Args:
            current_time (int): 현재 시뮬레이션 틱 (시간) 입니다.

        Returns:
            List[Transaction]: 주문 매칭 결과로 생성된 거래(Transaction) 객체들의 리스트입니다.
                              매칭된 거래가 없으면 빈 리스트를 반환합니다.
        """
        raise NotImplementedError

    @abstractmethod
    def get_daily_avg_price(self) -> float:
        """
        해당 시장의 일일 평균 거래 가격을 반환합니다.
        """
        pass

    @abstractmethod
    def get_daily_volume(self) -> float:
        """
        해당 시장의 일일 거래량을 반환합니다.
        """
        pass

    @abstractmethod
    def clear_orders(self) -> None:
        """현재 틱의 모든 주문을 초기화합니다."""
        pass
