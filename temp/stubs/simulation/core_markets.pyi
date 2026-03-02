import abc
import logging
from _typeshed import Incomplete
from abc import ABC, abstractmethod
from simulation.models import Order as Order, Transaction as Transaction

logger: Incomplete

class Market(ABC, metaclass=abc.ABCMeta):
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
    id: Incomplete
    matched_transactions: list[Transaction]
    logger: Incomplete
    def __init__(self, market_id: str, logger: logging.Logger | None = None) -> None: ...
    @abstractmethod
    def place_order(self, order: Order, current_time: int) -> list[Transaction]:
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
    @abstractmethod
    def match_orders(self, current_time: int) -> list[Transaction]:
        """
        현재 시장에 제출된 매수/매도 주문들을 매칭하여 거래를 생성합니다.
        이 메서드는 하위 클래스에서 반드시 구현되어야 합니다.

        Args:
            current_time (int): 현재 시뮬레이션 틱 (시간) 입니다.

        Returns:
            List[Transaction]: 주문 매칭 결과로 생성된 거래(Transaction) 객체들의 리스트입니다.
                              매칭된 거래가 없으면 빈 리스트를 반환합니다.
        """
    @abstractmethod
    def get_daily_avg_price(self) -> float:
        """
        해당 시장의 일일 평균 거래 가격을 반환합니다.
        """
    @abstractmethod
    def get_daily_volume(self) -> float:
        """
        해당 시장의 일일 거래량을 반환합니다.
        """
    @abstractmethod
    def clear_orders(self) -> None:
        """현재 틱의 모든 주문을 초기화합니다."""
