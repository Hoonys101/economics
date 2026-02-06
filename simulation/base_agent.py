from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING
import logging
from modules.finance.api import InsufficientFundsError
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY, ICurrencyHolder # Added for Phase 33
from modules.finance.wallet.wallet import Wallet
from modules.finance.wallet.api import IWallet
from modules.simulation.api import IInventoryHandler

if TYPE_CHECKING:
    from modules.memory.api import MemoryV2Interface


class BaseAgent(ICurrencyHolder, IInventoryHandler, ABC):
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

        initial_balance_dict = {}
        if isinstance(initial_assets, dict):
            initial_balance_dict = initial_assets.copy()
        else:
            initial_balance_dict[DEFAULT_CURRENCY] = float(initial_assets)

        self._wallet = Wallet(self.id, initial_balance_dict)

        self.needs = initial_needs
        self.decision_engine = decision_engine
        self.value_orientation = value_orientation
        self.name = name if name is not None else f"{self.__class__.__name__}_{id}"
        self._inventory: Dict[str, float] = {}
        self.is_active: bool = True
        self.logger = logger if logger is not None else logging.getLogger(self.name)
        self._pre_state_data: Dict[str, Any] = {}  # 이전 상태 저장을 위한 속성
        self.pre_state_snapshot: Dict[str, Any] = {} # Mypy fix: Snapshot for learning

    @property
    def inventory(self) -> Dict[str, float]:
        """
        [DEPRECATED] Read-only backward compatibility accessor for _inventory.
        External systems should transition to using IInventoryHandler methods.
        """
        return self._inventory.copy()

    # Setter removed to enforce IInventoryHandler protocol usage (TD-256)
    # def inventory(self, value): ...

    @property
    def wallet(self) -> IWallet:
        return self._wallet

    @property
    def assets(self) -> Dict[CurrencyCode, float]:
        """Current assets keyed by currency (Read-Only)."""
        return self._wallet.get_all_balances()

    def get_assets_by_currency(self) -> Dict[CurrencyCode, float]:
        """Implementation of ICurrencyHolder."""
        return self._wallet.get_all_balances()

    def _internal_add_assets(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        [INTERNAL ONLY] Increase assets.
        """
        self._wallet.add(amount, currency, memo="Internal Add")

    def _internal_sub_assets(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        [INTERNAL ONLY] Decrease assets.
        """
        # Checks are handled by Wallet.subtract unless allow_negative_balance is True
        self._wallet.subtract(amount, currency, memo="Internal Sub")

    def deposit(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deposits a given amount into the entity's account."""
        if amount > 0:
            self._wallet.add(amount, currency, memo="Deposit")

    def withdraw(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        Withdraws a given amount from the entity's account.
        """
        if amount > 0:
            # Wallet raises InsufficientFundsError automatically
            self._wallet.subtract(amount, currency, memo="Withdraw")

    # --- IInventoryHandler Implementation ---

    def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, quality: float = 1.0) -> bool:
        """
        Adds item to inventory safely.
        """
        if quantity < 0:
            self.logger.warning(f"INVENTORY_FAIL | Attempt to add negative quantity {quantity} of {item_id}")
            return False

        current = self._inventory.get(item_id, 0.0)
        self._inventory[item_id] = current + quantity
        return True

    def remove_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None) -> bool:
        """
        Removes item from inventory safely. Returns False if insufficient.
        """
        if quantity < 0:
            self.logger.warning(f"INVENTORY_FAIL | Attempt to remove negative quantity {quantity} of {item_id}")
            return False

        current = self._inventory.get(item_id, 0.0)
        if current < quantity:
            self.logger.warning(f"INVENTORY_FAIL | Insufficient {item_id}. Have {current}, Need {quantity}")
            return False

        self._inventory[item_id] = current - quantity
        if self._inventory[item_id] <= 1e-9: # Cleanup logic
             del self._inventory[item_id]

        return True

    def get_quantity(self, item_id: str) -> float:
        return self._inventory.get(item_id, 0.0)

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
