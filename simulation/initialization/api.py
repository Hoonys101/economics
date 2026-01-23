from __future__ import annotations
from typing import List, Dict, Any
import logging


# Forward declaration to avoid circular import
class Simulation:
    pass


class SimulationInitializerInterface:
    """Simulation 인스턴스 생성을 책임지는 인터페이스"""

    def build_simulation(self) -> Simulation:
        """
        모든 구성 요소를 조립하여 완전히 준비된 Simulation 인스턴스를 반환합니다.
        """
        ...
