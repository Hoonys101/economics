from modules.system.api import IGlobalRegistry as IGlobalRegistry
from simulation.dtos.telemetry import TelemetrySnapshotDTO

class TelemetryCollector:
    """
    시뮬레이션 상태 데이터를 선별적으로 수집하는 엔진.
    Selectively collects simulation state data based on dot-notation masks.
    """
    def __init__(self, registry: IGlobalRegistry) -> None: ...
    def subscribe(self, mask: list[str], frequency_interval: int = 1):
        """
        수집할 필드와 틱 단위 주기를 등록.
        Registers fields and tick frequency for collection.
        Performs pre-validation of paths.
        """
    def unsubscribe(self, mask: list[str]):
        """
        구독 해제.
        Unsubscribe from fields.
        """
    def update_subscriptions(self, mask: list[str]):
        """
        구독 리스트 전체 교체 (On-Demand Telemetry).
        Replaces the current subscription list with a new mask.
        Optimized to retain existing accessors if paths overlap.
        """
    def harvest(self, current_tick: int) -> TelemetrySnapshotDTO:
        """
        현재 틱에서 수집 주기가 도래한 데이터들만 추출.
        Collects data for fields whose frequency interval matches the current tick.
        """
