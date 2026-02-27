from _typeshed import Incomplete
from modules.demographics.genealogy.dtos import AncestorDTO as AncestorDTO, DescendantDTO as DescendantDTO, GenealogyNodeDTO as GenealogyNodeDTO, GenealogyTreeDTO as GenealogyTreeDTO
from modules.system.api import IAgentRegistry as IAgentRegistry

class GenealogyService:
    agent_registry: Incomplete
    def __init__(self, agent_registry: IAgentRegistry) -> None: ...
    def get_ancestors(self, agent_id: int) -> list[AncestorDTO]:
        """
        Returns a list of ancestors for the given agent ID, ordered by generation gap.
        """
    def get_descendants(self, agent_id: int) -> list[DescendantDTO]:
        """
        Returns a list of all descendants (children, grandchildren, etc.) for the given agent ID.
        """
    def get_tree(self, root_id: int, depth: int = 3) -> GenealogyTreeDTO:
        """
        Returns a genealogy tree starting from the root_id, traversing downwards (descendants).
        """
