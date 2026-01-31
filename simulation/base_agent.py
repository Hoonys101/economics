from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING
import logging
from modules.finance.api import InsufficientFundsError

if TYPE_CHECKING:
    from modules.memory.api import MemoryV2Interface


class BaseAgent(ABC):
    def __init__(
        self,
        id: int,
        initial_assets: float,
        initial_needs: Dict[str, float],
        decision_engine: Any,
        value_orientation: str,
        name: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        memory_interface: Optional["MemoryV2Interface"] = None,
    ):
        self.id = id
        self._assets = initial_assets
        self.needs = initial_needs
        self.decision_engine = decision_engine
        self.value_orientation = value_orientation
        self.name = name if name is not None else f"{self.__class__.__name__}_{id}"
        self.inventory: Dict[str, float] = {}
        self.is_active: bool = True
        self.logger = logger if logger is not None else logging.getLogger(self.name)
        self._pre_state_data: Dict[str, Any] = {}  # 이전 상태 저장을 위한 속성
        self.pre_state_snapshot: Dict[str, Any] = {} # Mypy fix: Snapshot for learning
        try:
            self.generation: int = 0
        except AttributeError:
            # If generation is a property (e.g. in Household), it cannot be set here.
            pass
        
        # [Cleanup] Standardized Memory Structure
        self.memory: Dict[str, Any] = {}
        self.memory_v2 = memory_interface

    @property
    def assets(self) -> float:
        """Current assets (Read-Only)."""
        return self._assets

    def _add_assets(self, amount: float) -> None:
        """
        [INTERNAL ONLY] Increase assets.
        MUST ONLY BE CALLED BY:
        1. SettlementSystem.transfer (Normal Operation)
        2. System Managers for Minting (e.g. Bank Credit Creation, Reflux Alchemy) WITH corresponding Ledger Update.

        DO NOT CALL DIRECTLY for standard transfers. Use SettlementSystem.
        """
        self._assets += amount

    def _sub_assets(self, amount: float) -> None:
        """
        [INTERNAL ONLY] Decrease assets.
        MUST ONLY BE CALLED BY:
        1. SettlementSystem.transfer (Normal Operation)

        DO NOT CALL DIRECTLY. Use SettlementSystem.
        """
        self._assets -= amount

    def deposit(self, amount: float) -> None:
        """Deposits a given amount into the entity's account."""
        if amount > 0:
            self._add_assets(amount)

    def withdraw(self, amount: float) -> None:
        """
        Withdraws a given amount from the entity's account.

        Raises:
            InsufficientFundsError: If the withdrawal amount exceeds available funds.
        """
        if amount > 0:
            if self.assets < amount:
                raise InsufficientFundsError(f"Agent {self.id} has insufficient funds for withdrawal of {amount:.2f}. Available: {self.assets:.2f}")
            self._sub_assets(amount)

    def get_agent_data(self) -> Dict[str, Any]:
        """AI 의사결정에 필요한 에이전트의 현재 상태 데이터를 반환합니다."""
        # 이 메서드는 하위 클래스에서 구체적인 내용을 구현해야 합니다.
        raise NotImplementedError

    def get_pre_state_data(self) -> Dict[str, Any]:
        """이전 틱의 에이전트 상태 데이터를 반환합니다."""
        return self._pre_state_data

    def update_pre_state_data(self):
        """현재 상태 데이터를 다음 틱을 위해 이전 상태 데이터로 저장합니다."""
        self._pre_state_data = self.get_agent_data()

    @abstractmethod
    def update_needs(self, current_tick: int):
        pass

    @abstractmethod
    def make_decision(self, input_dto: Any) -> tuple[list[Any], Any]:
        pass

    @abstractmethod
    def clone(self, new_id: int, initial_assets_from_parent: float, current_tick: int) -> "BaseAgent":
        """
        현재 에이전트 인스턴스를 복제하여 새로운 에이전트를 생성합니다.
        AI 모델(decision_engine)을 포함하여 깊은 복사를 수행합니다.
        initial_assets_from_parent: 복제될 에이전트가 부모 에이전트로부터 물려받을 초기 자산.
        """
        pass
