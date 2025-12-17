"""
Configuration management for lazyi18n.
Supports both global and local (project-specific) configuration.
"""

from pathlib import Path
from typing import Any, Optional
import tomli
import tomli_w


class Config:
    """Manages lazyi18n configuration."""

    def __init__(self, project_dir: Optional[Path] = None):
        """
        Initialize config manager.
        
        Args:
            project_dir: Project directory for local config. If None, only global config is used.
        """
        self.project_dir = Path(project_dir) if project_dir else None
        self._config = {}
        self._load()

    @staticmethod
    def get_global_config_path() -> Path:
        """Get the path to the global config file."""
        config_home = Path.home() / ".config" / "lazyi18n"
        config_home.mkdir(parents=True, exist_ok=True)
        return config_home / "config.toml"

    def get_local_config_path(self) -> Optional[Path]:
        """Get the path to the local config file."""
        if not self.project_dir:
            return None
        return self.project_dir / ".lazyi18n" / "config.toml"

    def _load(self) -> None:
        """Load configuration from global and local files."""
        self._config = {}

        # Load global config
        global_path = self.get_global_config_path()
        if global_path.exists():
            try:
                with open(global_path, "rb") as f:
                    self._config.update(tomli.load(f))
            except Exception as e:
                print(f"Warning: Failed to load global config: {e}")

        # Load local config (overrides global)
        local_path = self.get_local_config_path()
        if local_path and local_path.exists():
            try:
                with open(local_path, "rb") as f:
                    self._config.update(tomli.load(f))
            except Exception as e:
                print(f"Warning: Failed to load local config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key (supports dot notation, e.g., "translator.api_key")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        parts = key.split(".")
        value = self._config
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        
        return value

    def set(self, key: str, value: Any, local: bool = False) -> bool:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
            local: If True, save to local config; otherwise global
            
        Returns:
            True if successful
        """
        # Update in-memory config
        parts = key.split(".")
        config_dict = self._config
        
        for part in parts[:-1]:
            if part not in config_dict:
                config_dict[part] = {}
            config_dict = config_dict[part]
        
        config_dict[parts[-1]] = value

        # Save to file
        return self._save(local)

    def _save(self, local: bool = False) -> bool:
        """
        Save configuration to file.
        
        Args:
            local: If True, save to local config; otherwise global
            
        Returns:
            True if successful
        """
        if local:
            path = self.get_local_config_path()
            if not path:
                print("Error: No project directory specified for local config")
                return False
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path = self.get_global_config_path()
            path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "wb") as f:
                tomli_w.dump(self._config, f)
            return True
        except Exception as e:
            print(f"Error: Failed to save config: {e}")
            return False

    def list_all(self) -> dict:
        """
        Get all configuration values.
        
        Returns:
            Dictionary of all config values
        """
        return self._config.copy()

    def delete(self, key: str, local: bool = False) -> bool:
        """
        Delete a configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            local: If True, delete from local config; otherwise global
            
        Returns:
            True if successful
        """
        parts = key.split(".")
        config_dict = self._config
        
        # Navigate to parent
        for part in parts[:-1]:
            if part not in config_dict:
                return False
            config_dict = config_dict[part]
        
        # Delete key
        if parts[-1] in config_dict:
            del config_dict[parts[-1]]
            return self._save(local)
        
        return False
