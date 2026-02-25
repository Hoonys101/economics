from _typeshed import Incomplete
from enum import Enum
from pathlib import Path

META: str
GUARDRAILS: str
OUTPUT_DISCIPLINE: str
WORKER_MODEL_MAP: Incomplete
DEFAULT_MODELS: Incomplete

def construct_mission_prompt(key: str, title: str, instruction_raw: str) -> str:
    """
    Constructs the full mission prompt by injecting protocols.
    """

class ArtifactType(Enum):
    SPEC = 'spec'
    AUDIT = 'audit'
    REVIEW = 'review'
    REPORT = 'report'

def get_artifact_path(mission_key: str, artifact_type: ArtifactType) -> Path:
    """
    Centralized resolver for mission artifacts.
    Enforces UPS-4.2 Directory Structure.
    """
