from pydantic import BaseModel

class AncestorDTO(BaseModel):
    id: int
    generation_gap: int
    name: str | None
    is_alive: bool

class DescendantDTO(BaseModel):
    id: int
    generation_gap: int
    name: str | None
    is_alive: bool

class GenealogyNodeDTO(BaseModel):
    id: int
    parent_id: int | None
    children_ids: list[int]
    generation: int
    name: str | None
    is_alive: bool

class GenealogyTreeDTO(BaseModel):
    root_id: int
    nodes: list[GenealogyNodeDTO]
