import json
import os
import threading
import platform
import logging
import aiofiles

# This is a singleton class to manage the configuration of the application.
class ConfigManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, config_path="server/src/config.json"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigManager, cls).__new__(cls)
                cls._instance.config_path = config_path
                cls._instance.config = {}
                cls._instance.initialized = False
            return cls._instance

    async def init(self) -> None:
        if self.initialized:
            return
        # make sure the directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        try:
            if os.path.exists(self.config_path):
                async with aiofiles.open(self.config_path, "r", encoding="utf-8") as f:
                    content = await f.read()
                    self.config = json.loads(content)
            else:
                self.config = self.get_default_config()
                await self.save_config()
        except Exception as e:
            logging.error(f"init configuration error: {e}")
            self.config = self.get_default_config()
        self.initialized = True

    def get_default_config(self) -> dict:
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

    async def save_config(self) -> None:
        try:
            async with aiofiles.open(self.config_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(self.config, indent=2))
        except Exception as e:
            logging.error(f"save configuration error: {e}")
            raise e

    async def get_config(self) -> dict:
        await self.init()
        return self.config.copy()

    async def get_value(self, key: str):
        await self.init()
        return self.config.get(key)

    async def set_value(self, key: str, value) -> None:
        await self.init()
        #TODO: 这里有问题，当 telemetryEnabled 由 True 变为 False 时，执行特殊处理
        if key == "telemetryEnabled" and value is False:
            current_value = self.config.get(key)
            if current_value is not False:
                logging.info(f"捕获 telemetry opt-out 事件，原值: {current_value}")
        self.config[key] = value
        await self.save_config()

    async def update_config(self, updates: dict) -> dict:
        await self.init()
        self.config.update(updates)
        await self.save_config()
        return self.config.copy()

    async def reset_config(self) -> dict:
        self.config = self.get_default_config()
        await self.save_config()
        return self.config.copy()