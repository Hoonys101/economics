from __future__ import annotations
from typing import List, Dict, Any, Tuple, TYPE_CHECKING, Optional, Union
from simulation.models import Order
from simulation.dtos import DecisionContext, DecisionOutputDTO

if TYPE_CHECKING:
    from simulation.core_markets import Market
    from simulation.dtos import MacroFinancialContext


class BaseDecisionEngine:
    def make_decisions(
        self,
        context: DecisionContext,
        macro_context: Optional[MacroFinancialContext] = None,
    ) -> DecisionOutputDTO:
        """
        에이전트의 현재 상태와 시장 정보를 바탕으로 의사결정을 내립니다.
        🚨 DTO PURITY GATE 🚨: 직접적인 에이전트 인스턴스 접근을 차단합니다.
        """
        # 🚨 DTO PURITY GATE 🚨
        assert hasattr(context, 'state') and context.state is not None, "Purity Error: context.state DTO is missing."
        assert hasattr(context, 'config') and context.config is not None, "Purity Error: context.config DTO is missing."
        
        return self._make_decisions_internal(context, macro_context)

    def _make_decisions_internal(
        self,
        context: DecisionContext,
        macro_context: Optional[MacroFinancialContext] = None,
    ) -> DecisionOutputDTO:
        """
        실제 의사결정 로직을 구현하는 내부 메서드.
        하위 클래스에서 반드시 구현해야 합니다.
        """
        raise NotImplementedError
