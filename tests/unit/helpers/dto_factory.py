from typing import Dict, List, Optional, Any
from simulation.models import Order, Transaction
from simulation.dtos.api import MarketSnapshotDTO
from modules.memory.V2.dtos import MemoryRecordDTO

class DTOFactory:
    @staticmethod
    def create_order(
        agent_id: int = 1,
        order_type: str = "BUY",
        item_id: str = "food",
        quantity: float = 1.0,
        price: float = 10.0,
        market_id: str = "test_market",
        target_agent_id: Optional[int] = None,
        brand_info: Optional[Dict[str, Any]] = None
    ) -> Order:
        return Order(
            agent_id=agent_id,
            order_type=order_type,
            item_id=item_id,
            quantity=quantity,
            price=price,
            market_id=market_id,
            target_agent_id=target_agent_id,
            brand_info=brand_info
        )

    @staticmethod
    def create_transaction(
        buyer_id: int = 1,
        seller_id: int = 2,
        item_id: str = "food",
        quantity: float = 1.0,
        price: float = 10.0,
        market_id: str = "test_market",
        transaction_type: str = "goods",
        time: int = 0,
        quality: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        return Transaction(
            buyer_id=buyer_id,
            seller_id=seller_id,
            item_id=item_id,
            quantity=quantity,
            price=price,
            market_id=market_id,
            transaction_type=transaction_type,
            time=time,
            quality=quality,
            metadata=metadata
        , total_pennies=int(price * quantity * 100))

    @staticmethod
    def create_market_snapshot(
        prices: Optional[Dict[str, float]] = None,
        volumes: Optional[Dict[str, float]] = None,
        asks: Optional[Dict[str, List[Order]]] = None,
        best_asks: Optional[Dict[str, float]] = None
    ) -> MarketSnapshotDTO:
        return MarketSnapshotDTO(
            prices=prices if prices is not None else {},
            volumes=volumes if volumes is not None else {},
            asks=asks if asks is not None else {},
            best_asks=best_asks if best_asks is not None else {}
        )

    @staticmethod
    def create_memory_record(
        tick: int = 0,
        agent_id: int = 1,
        event_type: str = "test_event",
        data: Optional[Dict[str, Any]] = None
    ) -> MemoryRecordDTO:
        return MemoryRecordDTO(
            tick=tick,
            agent_id=agent_id,
            event_type=event_type,
            data=data if data is not None else {}
        )
