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

    async def init(self) -> None:
        if self.initialized:
            return
        if self._config_path:
            await self._load_config()

        self.initialized = True

    @staticmethod
    def _get_default_config() -> dict:
        return {
            "blockedCommands": [
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
            "defaultShell": "powershell.exe" if platform.system().lower() == "windows" else "bash",
            "allowed_directories": [],
            "telemetryEnabled": True
        }

    async def _load_config(self) -> None:
        try:
            async with aiofiles.open(self._config_path, "r", encoding="utf-8") as f:
                self._config = json.loads(await f.read())
                self._config_path = os.path.abspath(self._config_path)
                logging.info(f"configuration loaded from {self._config_path}")
        except FileNotFoundError:
            logging.error(f"configuration file not found, using default configuration")
        except Exception as e:
            logging.error(f"error loading configuration: {e}")
            raise e
        print(2)

    async def save_config(self, save_path: Optional[str] = None) -> None:
        save_path = save_path or self._config_path
        if not save_path:
            logging.error("No path provided to save the configuration.")
            raise ValueError("No path provided to save the configuration.")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        try:
            async with aiofiles.open(save_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(self._config, indent=2))
        except Exception as e:
            logging.error(f"save configuration error: {e}")
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
    

# async def main():
#     # 初始化时指定配置文件路径
#     manager = ConfigManager(config_path="/Users/tangbingbing/workspace/mcp/mcp_fs_dm/server/src/config.json")
#     print(manager.config)  # 显示默认配置
#     # 显式初始化加载配置
#     await manager.init()
#     print(manager.config)  # 显示默认配置

    
#     # 修改配置
#     manager.update_config({
#         "telemetryEnabled": False,
#         "allowed_directories": ["/safe/path"]
#     })
    
#     # 保存到初始化路径
#     # await manager.save_config(save_path="./config2.json")
    
#     # 创建新实例会得到同一个单例
#     # new_manager = ConfigManager()
#     # print(new_manager.config)  # 显示修改后的配置

# # 异步运行示例
# import asyncio
# asyncio.run(main())