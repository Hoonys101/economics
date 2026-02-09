from __future__ import annotations
from typing import List, TYPE_CHECKING
from modules.finance.api import ITaxService
from modules.common.dtos import Claim
from modules.system.api import DEFAULT_CURRENCY

if TYPE_CHECKING:
    from simulation.firms import Firm
    from modules.system.api import IAgentRegistry

class TaxService(ITaxService):
    def __init__(self, agent_registry: IAgentRegistry):
        self.agent_registry = agent_registry

    def calculate_liquidation_tax_claims(self, firm: Firm) -> List[Claim]:
        claims = []
        tax_rate = getattr(firm.config, "corporate_tax_rate", 0.0)

        current_profit_raw = firm.finance_state.current_profit
        current_profit = current_profit_raw
        if isinstance(current_profit_raw, dict):
            current_profit = current_profit_raw.get(DEFAULT_CURRENCY, 0.0)

        if current_profit > 0:
            tax_liability = current_profit * tax_rate

            # Find Government ID
            gov_agent = self.agent_registry.get_agent("government")
            gov_id = "government"
            if gov_agent:
                gov_id = gov_agent.id

            claims.append(Claim(
                creditor_id=gov_id,
                amount=tax_liability,
                tier=3,
                description="Corporate Tax"
            ))

        return claims
