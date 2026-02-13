from __future__ import annotations
import time
from typing import List, Dict, Any, Optional, Callable, Set
from modules.system.api import IGlobalRegistry
from simulation.dtos.telemetry import TelemetrySnapshotDTO

class TelemetryCollector:
    """
    시뮬레이션 상태 데이터를 선별적으로 수집하는 엔진.
    Selectively collects simulation state data based on dot-notation masks.
    """

    def __init__(self, registry: IGlobalRegistry):
        self._registry = registry
        self._subscriptions: Dict[str, int] = {}  # field_path: frequency_interval
        # Cache resolved accessors to avoid repeated traversal overhead
        self._accessors: Dict[str, Callable[[], Any]] = {}
        # Track invalid paths separately
        self._invalid_paths: Set[str] = set()

    def subscribe(self, mask: List[str], frequency_interval: int = 1):
        """
        수집할 필드와 틱 단위 주기를 등록.
        Registers fields and tick frequency for collection.
        Performs pre-validation of paths.
        """
        for path in mask:
            self._subscriptions[path] = frequency_interval

            # Attempt to resolve accessor (Pre-validation)
            accessor = self._resolve_path(path)
            if accessor:
                self._accessors[path] = accessor
                if path in self._invalid_paths:
                    self._invalid_paths.remove(path)
            else:
                self._invalid_paths.add(path)
                self._accessors.pop(path, None)

    def unsubscribe(self, mask: List[str]):
        """
        구독 해제.
        Unsubscribe from fields.
        """
        for path in mask:
            self._subscriptions.pop(path, None)
            self._accessors.pop(path, None)
            if path in self._invalid_paths:
                self._invalid_paths.remove(path)

    def update_subscriptions(self, mask: List[str]):
        """
        구독 리스트 전체 교체 (On-Demand Telemetry).
        Replaces the current subscription list with a new mask.
        Optimized to retain existing accessors if paths overlap.
        """
        # Identify paths to remove
        current_paths = set(self._subscriptions.keys())
        new_paths = set(mask)

        to_remove = current_paths - new_paths
        to_add = new_paths - current_paths

        # Remove old subscriptions
        if to_remove:
            self.unsubscribe(list(to_remove))

        # Add new subscriptions
        if to_add:
            self.subscribe(list(to_add), frequency_interval=1) # Default to 1 tick for on-demand

    def harvest(self, current_tick: int) -> TelemetrySnapshotDTO:
        """
        현재 틱에서 수집 주기가 도래한 데이터들만 추출.
        Collects data for fields whose frequency interval matches the current tick.
        """
        data: Dict[str, Any] = {}
        errors: List[str] = []

        for path, interval in self._subscriptions.items():
            if current_tick % interval == 0:
                if path in self._accessors:
                    try:
                        data[path] = self._accessors[path]()
                    except Exception:
                        # Runtime error during access (e.g., attribute missing later)
                        errors.append(path)
                elif path in self._invalid_paths:
                    errors.append(path)
                else:
                    # Fallback for paths that were neither resolved nor marked invalid (should not happen)
                    errors.append(path)

        snapshot: TelemetrySnapshotDTO = {
            "timestamp": time.time(),
            "tick": current_tick,
            "data": data,
            "errors": errors,
            "metadata": {
                "collected_count": len(data),
                "error_count": len(errors)
            }
        }
        return snapshot

    def _create_accessor(self, path: str) -> Callable[[], Any]:
        """
        Creates a callable that traverses the path from the registry.
        """
        parts = path.split('.')
        root_key = parts[0]
        sub_path = parts[1:]

        def accessor():
            # Get root object from registry
            current = self._registry.get(root_key)
            if current is None:
                raise AttributeError(f"Root key '{root_key}' not found in registry")

            # Traverse
            for part in sub_path:
                if current is None:
                     # Attempting to access attribute of None
                     raise AttributeError(f"Cannot access attribute '{part}' of None (in path '{path}')")

                if isinstance(current, dict):
                    if part not in current:
                        raise KeyError(f"Key '{part}' not found in dictionary (in path '{path}')")
                    current = current[part]
                else:
                    if not hasattr(current, part):
                        raise AttributeError(f"Object has no attribute '{part}' (in path '{path}')")
                    current = getattr(current, part)
            return current

        return accessor

    def _resolve_path(self, path: str) -> Optional[Callable[[], Any]]:
        """
        GlobalRegistry에서 Dot-notation 경로로 값을 조회하는 접근자를 생성.
        Resolves a dot-notation path into a callable accessor.
        Validates access once immediately.
        """
        if not path:
            return None

        # Strategy 1: Try full path as a Key-Value pair (FOUND-01 Support)
        # This handles cases where keys are stored flat (e.g. "government.tax_rate")
        try:
            # We use a distinct default to check existence, assuming registry doesn't store this sentinel
            sentinel = object()
            val = self._registry.get(path, default=sentinel)
            if val is not sentinel:
                return lambda: self._registry.get(path)
        except Exception:
            pass

        # Strategy 2: Try object traversal (Deep Access)
        try:
            accessor = self._create_accessor(path)
            # Validation: try to access once
            accessor()
            return accessor
        except Exception:
            return None
