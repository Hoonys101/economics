from typing import List, Optional, Any, TYPE_CHECKING
import logging

from simulation.dtos.agents import AgentBasicDTO, AgentDetailDTO
from simulation.core_agents import Household
from simulation.firms import Firm
from modules.simulation.api import IAgent, IOrchestratorAgent, ISensoryDataProvider

if TYPE_CHECKING:
    from simulation.engine import Simulation

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self, simulation: "Simulation"):
        self.simulation = simulation

    def get_agents_basic(self, limit: int = 500) -> List[AgentBasicDTO]:
        """
        Returns a lightweight list of agents for scatter plot visualization.
        Uses IAgent/IOrchestratorAgent protocols for type safety.
        """
        if not self.simulation or not self.simulation.world_state:
            return []

        agents = []
        count = 0

        # Access agents directly from the registry/world_state
        # Assuming world_state.agents is Dict[int, IAgent]
        all_agents = self.simulation.world_state.agents.values()

        for agent in all_agents:
            # Protocol-based check
            if isinstance(agent, IAgent):
                if not agent.is_active:
                    continue
            else:
                # If agent doesn't implement IAgent (e.g. system agents?), skip or include based on policy
                # For scatter plot, we only care about entities with wealth/income (Households/Firms)
                # which are IOrchestratorAgent usually.
                pass

            # Only map known types that implement required properties
            if isinstance(agent, (Household, Firm)):
                 dto = self._map_to_basic_dto(agent)
                 if dto:
                    agents.append(dto)
                    count += 1
                    if count >= limit:
                        break

        return agents

    def get_agent_detail(self, agent_id: int) -> Optional[AgentDetailDTO]:
        """
        Returns detailed information for a specific agent.
        """
        if not self.simulation or not self.simulation.world_state:
            return None

        agent = self.simulation.world_state.agents.get(agent_id)
        if not agent:
            return None

        return self._map_to_detail_dto(agent)

    def _map_to_basic_dto(self, agent: Any) -> Optional[AgentBasicDTO]:
        try:
            if isinstance(agent, Household):
                return AgentBasicDTO(
                    id=agent.id,
                    type="household",
                    wealth=agent.total_wealth,
                    income=agent.labor_income_this_tick,
                    expense=agent._econ_state.consumption_expenditure_this_tick_pennies
                )
            elif isinstance(agent, Firm):
                # Calculate total expense for this tick across all currencies (simplified sum for visualization)
                expense = sum(agent.finance_state.expenses_this_tick.values())
                # Calculate total revenue for this turn
                income = sum(agent.finance_state.revenue_this_turn.values())

                return AgentBasicDTO(
                    id=agent.id,
                    type="firm",
                    wealth=agent.total_wealth,
                    income=int(income),
                    expense=int(expense)
                )
        except Exception as e:
            logger.warning(f"Failed to map agent {agent.id} to basic DTO: {e}")
            return None
        return None

    def _map_to_detail_dto(self, agent: Any) -> Optional[AgentDetailDTO]:
        basic = self._map_to_basic_dto(agent)
        if not basic:
            return None

        try:
            if isinstance(agent, Household):
                return AgentDetailDTO(
                    **basic.model_dump(),
                    is_active=agent.is_active,
                    age=agent.age,
                    needs=agent._bio_state.needs,
                    inventory=agent.inventory,
                    employer_id=agent.employer_id,
                    current_wage=agent.current_wage
                )
            elif isinstance(agent, Firm):
                return AgentDetailDTO(
                    **basic.model_dump(),
                    is_active=agent.is_active,
                    sector=agent.sector,
                    employees_count=len(agent.hr_state.employees),
                    production=agent.current_production,
                    revenue_this_turn=agent.finance_state.revenue_this_turn,
                    expenses_this_tick=agent.finance_state.expenses_this_tick
                )
        except Exception as e:
            logger.warning(f"Failed to map agent {agent.id} to detail DTO: {e}")
            return None

        return None
