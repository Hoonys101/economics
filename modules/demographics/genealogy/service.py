from typing import List, Optional, Deque, Set
from collections import deque
from modules.system.api import IAgentRegistry
from modules.demographics.genealogy.dtos import AncestorDTO, DescendantDTO, GenealogyTreeDTO, GenealogyNodeDTO
from simulation.core_agents import Household

class GenealogyService:
    def __init__(self, agent_registry: IAgentRegistry):
        self.agent_registry = agent_registry

    def _get_agent(self, agent_id: int) -> Optional[Household]:
        """
        Retrieves a Household agent by ID from the registry.
        Returns None if not found or not a Household.
        """
        try:
            agent = self.agent_registry.get_agent(agent_id)
            if isinstance(agent, Household):
                return agent
        except Exception:
            # Registry might raise error if ID not found, depending on implementation.
            # Assuming safe get_agent or catch-all.
            pass
        return None

    def get_ancestors(self, agent_id: int) -> List[AncestorDTO]:
        """
        Returns a list of ancestors for the given agent ID, ordered by generation gap.
        """
        ancestors = []
        current_id = agent_id
        gap = 1

        while True:
            agent = self._get_agent(current_id)
            if not agent:
                break

            parent_id = agent.parent_id
            if parent_id is None:
                break

            parent = self._get_agent(parent_id)

            if parent:
                ancestors.append(AncestorDTO(
                    id=parent.id,
                    generation_gap=gap,
                    name=getattr(parent, "name", f"Household_{parent.id}"),
                    is_alive=parent.is_active
                ))
                current_id = parent_id
                gap += 1
            else:
                # Parent exists in record but not in registry (e.g. data lost or specialized archive)
                # We stop traversal here as we can't get further parents.
                break

        return ancestors

    def get_descendants(self, agent_id: int) -> List[DescendantDTO]:
        """
        Returns a list of all descendants (children, grandchildren, etc.) for the given agent ID.
        """
        descendants = []
        queue: Deque[tuple[int, int]] = deque([(agent_id, 1)]) # (id, gap)
        visited: Set[int] = {agent_id}

        while queue:
            curr_id, gap = queue.popleft()
            agent = self._get_agent(curr_id)
            if not agent:
                continue

            for child_id in agent.children_ids:
                if child_id in visited:
                    continue
                visited.add(child_id)

                child = self._get_agent(child_id)
                if child:
                    descendants.append(DescendantDTO(
                        id=child.id,
                        generation_gap=gap,
                        name=getattr(child, "name", f"Household_{child.id}"),
                        is_alive=child.is_active
                    ))
                    queue.append((child.id, gap + 1))

        return descendants

    def get_tree(self, root_id: int, depth: int = 3) -> GenealogyTreeDTO:
        """
        Returns a genealogy tree starting from the root_id, traversing downwards (descendants).
        """
        nodes = []
        queue: Deque[tuple[int, int]] = deque([(root_id, 0)])
        visited: Set[int] = set()

        while queue:
            curr_id, curr_depth = queue.popleft()

            if curr_id in visited:
                continue
            visited.add(curr_id)

            agent = self._get_agent(curr_id)
            if not agent:
                continue

            nodes.append(GenealogyNodeDTO(
                id=agent.id,
                parent_id=agent.parent_id,
                children_ids=agent.children_ids,
                generation=agent.generation,
                name=getattr(agent, "name", f"Household_{agent.id}"),
                is_alive=agent.is_active
            ))

            if curr_depth < depth:
                for child_id in agent.children_ids:
                    if child_id not in visited:
                        queue.append((child_id, curr_depth + 1))

        return GenealogyTreeDTO(root_id=root_id, nodes=nodes)
