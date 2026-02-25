from pathlib import Path

def resolve_manual_links(manual_text: str, current_manual_path: Path, base_dir: Path) -> list[str]:
    """Parses markdown links from manual and resolves them to absolute paths."""
def get_situational_manual_paths(changed_files: list[str]) -> list[str]:
    """
    Analyzes changed files and returns relevant architectural manual paths.
    """
def get_core_contract_paths(changed_files: list[str]) -> list[str]:
    """
    Returns relevant DTO and API contract paths based on changed files.
    """
