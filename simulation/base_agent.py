from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING, override
import logging
from modules.finance.api import InsufficientFundsError, IFinancialEntity, ICreditFrozen
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY, ICurrencyHolder # Added for Phase 33
from modules.finance.wallet.wallet import Wallet
from modules.finance.wallet.api import IWallet
from modules.simulation.api import IInventoryHandler
from simulation.dtos.agent_dtos import BaseAgentInitDTO

if TYPE_CHECKING:
    from modules.memory.api import MemoryV2Interface


class BaseAgent(ICurrencyHolder, IInventoryHandler, IFinancialEntity, ICreditFrozen, ABC):
    def __init__(
        self,
        init_config: BaseAgentInitDTO
    ):
        self.id = init_config.id
        self.memory_v2 = init_config.memory_interface
        self._credit_frozen_until_tick: int = 0

        initial_balance_dict = {}
        if isinstance(init_config.initial_assets, dict):
            initial_balance_dict = init_config.initial_assets.copy()
        else:
            initial_balance_dict[DEFAULT_CURRENCY] = float(init_config.initial_assets)

        self._wallet = Wallet(self.id, initial_balance_dict)

        self.needs = init_config.initial_needs
        self.decision_engine = init_config.decision_engine
        self.value_orientation = init_config.value_orientation
        self.name = init_config.name if init_config.name is not None else f"{self.__class__.__name__}_{self.id}"
        self._inventory: Dict[str, float] = {}
        self.is_active: bool = True
        self.logger = init_config.logger if init_config.logger is not None else logging.getLogger(self.name)
        self._pre_state_data: Dict[str, Any] = {}  # 이전 상태 저장을 위한 속성
        self.pre_state_snapshot: Dict[str, Any] = {} # Mypy fix: Snapshot for learning

    @property
    def wallet(self) -> IWallet:
        return self._wallet

    @property
    def assets(self) -> float:
        """Current assets in DEFAULT_CURRENCY (Read-Only). Implementation of IFinancialEntity."""
        return self._wallet.get_balance(DEFAULT_CURRENCY)

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

    # --- ICreditFrozen Implementation ---

    @property
    def credit_frozen_until_tick(self) -> int:
        return self._credit_frozen_until_tick

    @credit_frozen_until_tick.setter
    def credit_frozen_until_tick(self, value: int) -> None:
        self._credit_frozen_until_tick = value

    # --- IInventoryHandler Implementation ---

    def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, quality: float = 1.0) -> bool:
        """
        Adds item to inventory safely.
        NOTE: This default implementation does NOT track quality.
        Subclasses (Firm, Household) MUST override this to implement quality tracking (weighted average).
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

    def get_all_items(self) -> Dict[str, float]:
        """Returns a copy of the inventory."""
        return self._inventory.copy()

    def clear_inventory(self) -> None:
        """Clears the inventory."""
        self._inventory.clear()

    def get_quality(self, item_id: str) -> float:
        """
        Default implementation returns 1.0. Subclasses tracking quality should override.
        """
        return 1.0

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
