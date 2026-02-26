from typing import Dict, Any

def deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merges source dict into target dict.

    Args:
        target: The dictionary to be modified.
        source: The dictionary with updates.

    Returns:
        The updated target dictionary.
    """
    for key, value in source.items():
        if isinstance(value, dict) and key in target and isinstance(target[key], dict):
            deep_merge(target[key], value)
        else:
            target[key] = value
    return target
