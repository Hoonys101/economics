from simulation.core_markets import Market as Market
from simulation.dtos import DecisionContext as DecisionContext, DecisionOutputDTO as DecisionOutputDTO, MacroFinancialContext as MacroFinancialContext
from simulation.models import Order as Order

class BaseDecisionEngine:
    def make_decisions(self, context: DecisionContext, macro_context: MacroFinancialContext | None = None) -> DecisionOutputDTO:
        """
        에이전트의 현재 상태와 시장 정보를 바탕으로 의사결정을 내립니다.
        🚨 DTO PURITY GATE 🚨: 직접적인 에이전트 인스턴스 접근을 차단합니다.
        """
