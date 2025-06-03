import json
import os
import threading
import platform
import logging
import aiofiles
from typing import Optional

# This is a singleton class to manage the configuration of the application.
class ConfigManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, config_path: Optional[str] = None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigManager, cls).__new__(cls)
                cls._instance._config_path = config_path
                cls._instance._config = cls._get_default_config()
                cls._instance.initialized = False
            return cls._instance

    def init(self) -> None:
        if self.initialized:
            return
        if self._config_path:
            self._load_config()

        self.initialized = True

    @staticmethod
    def _get_default_config() -> dict:
        return {
            "blocked_commands": [
                "mkfs",
                "format",
                "mount",
                "umount",
                "fdisk",
                "dd",
                "parted",
                "diskpart",
                "sudo",
                "su",
                "passwd",
                "adduser",
                "useradd",
                "usermod",
                "groupadd",
                "chsh",
                "visudo",
                "shutdown",
                "reboot",
                "halt",
                "poweroff",
                "init",
                "iptables",
                "firewall",
                "netsh",
                "sfc",
                "bcdedit",
                "reg",
                "net",
                "sc",
                "runas",
                "cipher",
                "takeown"
            ],
            "default_shell": "powershell.exe" if platform.system().lower() == "windows" else "bash",
            "allowed_directories": [],
            "max_read_length": 1000,
        }

    def _load_config(self) -> None:
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
                self._config_path = os.path.abspath(self._config_path)
                logging.info(f"configuration loaded from {self._config_path}")
            if loaded_config.get("add_default_config", False):
                default_config = self._get_default_config()
                self._config = {**default_config, **loaded_config}
            else:
                self._config = loaded_config
        except FileNotFoundError:
            logging.warning(f"Configuration file not found at {self._config_path}, using default configuration")
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in configuration file: {e}")
            raise e
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
            raise e

    def save_config(self, save_path: Optional[str] = None) -> None:
        save_path = save_path or self._config_path
        if not save_path:
            logging.error("No path provided to save the configuration.")
            raise ValueError("No path provided to save the configuration.")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                 json.dump(self._config, f, indent=2, ensure_ascii=False)
            logging.info(f"Configuration saved to {save_path}")
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
            raise e

    @property
    def config(self) -> dict:
        return self._config.copy()

    def get_value(self, key: str):
        return self._config.get(key)

    def set_value(self, key: str, value) -> None:
        self._config[key] = value

    def update_config(self, updates: dict) -> dict:
        self._config.update(updates)
        return self._config.copy()

    def reset_config(self) -> dict:
        self._config = self._get_default_config()
        return self._config.copy()
    
    def get_allowed_directories(self) -> list:
        return self._config.get("allowed_directories", [])

def get_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """
    Get the singleton instance of ConfigManager.
    
    :param config_path: Optional path to the configuration file.
    :return: ConfigManager instance.
    """
    config = ConfigManager(config_path)
    if not config.initialized:
        config.init()
    else:
        logging.debug("ConfigManager already initialized.")
    return config