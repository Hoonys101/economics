from fastapi import APIRouter, HTTPException, Depends
from typing import List, Any
from modules.demographics.genealogy.service import GenealogyService
from modules.demographics.genealogy.dtos import AncestorDTO, DescendantDTO, GenealogyTreeDTO

# Dependency to get the service instance
def get_genealogy_service() -> GenealogyService:
    # Lazy import to avoid circular dependency
    try:
        from server import sim
    except ImportError:
        sim = None

    if not sim:
        raise HTTPException(status_code=503, detail="Simulation not initialized")

    # Assuming sim has agent_registry
    if not hasattr(sim, 'agent_registry') or not sim.agent_registry:
         raise HTTPException(status_code=503, detail="Agent Registry not available")

    return GenealogyService(sim.agent_registry)

router = APIRouter(prefix="/genealogy", tags=["Genealogy"])

@router.get("/{agent_id}/ancestors", response_model=List[AncestorDTO])
def get_ancestors(agent_id: int, service: GenealogyService = Depends(get_genealogy_service)):
    return service.get_ancestors(agent_id)

@router.get("/{agent_id}/descendants", response_model=List[DescendantDTO])
def get_descendants(agent_id: int, service: GenealogyService = Depends(get_genealogy_service)):
    return service.get_descendants(agent_id)

@router.get("/{agent_id}/tree", response_model=GenealogyTreeDTO)
def get_tree(agent_id: int, depth: int = 3, service: GenealogyService = Depends(get_genealogy_service)):
    return service.get_tree(agent_id, depth)
