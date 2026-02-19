from pydantic import BaseModel, Field
from typing import List, Optional

class AncestorDTO(BaseModel):
    id: int
    generation_gap: int
    name: Optional[str] = None
    is_alive: bool

class DescendantDTO(BaseModel):
    id: int
    generation_gap: int
    name: Optional[str] = None
    is_alive: bool

class GenealogyNodeDTO(BaseModel):
    id: int
    parent_id: Optional[int]
    children_ids: List[int] = Field(default_factory=list)
    generation: int
    name: Optional[str] = None
    is_alive: bool

class GenealogyTreeDTO(BaseModel):
    root_id: int
    nodes: List[GenealogyNodeDTO]
