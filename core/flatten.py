"""
Utilities for flattening/unflattening nested i18n JSON structures.
Converts between nested dicts and dot-notation for easier comparison.
"""

from typing import Dict, Any, Tuple


def flatten_json(
    data: Dict,
    parent_key: str = "",
    sep: str = ".",
) -> Dict[str, Any]:
    """
    Flatten nested JSON to dot-notation keys.
    
    Example:
        {"auth": {"login": {"btn": "Login"}}}
        -> {"auth.login.btn": "Login"}
    """
    items = []
    
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(
                flatten_json(value, new_key, sep=sep).items()
            )
        else:
            items.append((new_key, value))
    
    return dict(items)


def unflatten_json(
    data: Dict[str, Any],
    sep: str = ".",
) -> Dict:
    """
    Unflatten dot-notation keys back to nested structure.
    
    Example:
        {"auth.login.btn": "Login"}
        -> {"auth": {"login": {"btn": "Login"}}}
    """
    result = {}
    
    for key, value in data.items():
        parts = key.split(sep)
        current = result
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    return result


def get_nested_value(data: Dict, key: str, sep: str = ".") -> Any:
    """Get a value from nested dict using dot-notation key."""
    parts = key.split(sep)
    current = data
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    
    return current


def set_nested_value(
    data: Dict,
    key: str,
    value: Any,
    sep: str = ".",
) -> Dict:
    """Set a value in nested dict using dot-notation key."""
    parts = key.split(sep)
    current = data
    
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    
    current[parts[-1]] = value
    return data
