from typing import TypedDict, Dict, List, Any

class TelemetrySnapshotDTO(TypedDict):
    """
    실시간 데이터 스냅샷 구조.
    Represents a snapshot of telemetry data collected at a specific tick.
    """
    timestamp: float      # 실제 시간 (Unix)
    tick: int            # 시뮬레이션 틱
    data: Dict[str, Any] # 수집된 데이터 필드 (Dot-notation key)
    errors: List[str]    # 조회 실패한 필드 목록
    metadata: Dict[str, Any] # 샘플링 빈도 등 부가 정보
