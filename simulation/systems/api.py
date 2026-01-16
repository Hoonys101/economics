from __future__ import annotations
from typing import List

class Simulation:  # Forward declaration
    pass

class Household: # Forward declaration
    pass

class AgentLifecycleManagerInterface:
    """에이전트의 생명주기를 관리하는 인터페이스"""
    def process_lifecycle_events(self, sim_context: Simulation):
        """한 틱 동안 발생하는 모든 생명주기 관련 이벤트를 처리합니다."""
        ...
