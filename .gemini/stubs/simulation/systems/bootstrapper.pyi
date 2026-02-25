from _typeshed import Incomplete
from simulation.firms import Firm as Firm
from simulation.households import Household as Household
from typing import Any

logger: Incomplete

class Bootstrapper:
    """
    System responsible for initializing agents with necessary resources
    to prevent 'Deadlock at Birth' scenarios.

    Ref: WO-058 Economic CPR
    """
    MIN_CAPITAL: int
    INITIAL_INVENTORY: float
    @staticmethod
    def distribute_initial_wealth(central_bank: Any, target_agent: Any, amount: int, settlement_system: Any) -> None:
        """
        Transfers initial wealth from Central Bank to target agent.
        Ensures zero-sum integrity via SettlementSystem.
        Phase 33: Uses create_and_transfer for Central Bank to ensure M2 Expansion is recorded.
        """
    @staticmethod
    def force_assign_workers(firms: list['Firm'], households: list['Household']) -> int: ...
    @staticmethod
    def inject_liquidity_for_firm(firm: Firm, config: Any, settlement_system: Any, central_bank: Any, current_tick: int = 0) -> bool:
        """
        Injects liquidity (inputs and capital) for a single firm.
        Returns True if any resource was injected.

        Zero-Sum Compliance:
        - Capital is transferred from Central Bank.
        - Physical Goods (Inputs) are only magically created at Tick 0 (Genesis).
        """
    @staticmethod
    def inject_initial_liquidity(firms: list['Firm'], config: Any, settlement_system: Any = None, central_bank: Any = None) -> None:
        """
        Injects a 30-tick buffer of raw materials and minimum capital.
        """
