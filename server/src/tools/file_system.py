import logging
import os
from server.src.config import ConfigManager

async def get_allowed_dirs() -> list:
    """
    Get the allowed directories from configuration
    """
    try:
        config = ConfigManager()
        await config.init()
        allowed_dirs = config.config.get("allowed_directories", [])
        # If no allowed dirs are set, use the home directory
        if not allowed_dirs:
            allowed_dirs = [os.environ['HOME']]
            await ConfigManager.set_value(config,"allowed_directories", allowed_dirs)
        allowed_dirs = [normalize_path(p) for p in allowed_dirs]
        return allowed_dirs
    except Exception as e:
        logging.error(f"Error getting allowed dirs:{e}")
    return []

def normalize_path(path: str) -> str:
    if path.startswith("~") or path == '~':
        # Expand the home directory
        path = os.path.expanduser(path)
    return path.rstrip(os.sep)

def validate_parent_dirs(path: str) -> bool:
    """
    Recursively validates parent directories until it finds a valid one
    @param path: The path to validate
    @return: True if the parent directory exists, False otherwise
    """
    parent = os.path.dirname(path)
    if parent == path or parent == os.path.dirname(parent):
        return False
    if os.path.exists(parent):
        return True
    return validate_parent_dirs(parent)

async def is_path_allowed(path: str) -> bool:
    """
    Check if the path is allowed to access
    """
    allowed_dirs = await get_allowed_dirs()
    if "/" in allowed_dirs or not allowed_dirs:
        # If the allowed dirs are empty or contain "/", allow all paths
        return True
    path = normalize_path(path)
    for allowed_dir in allowed_dirs:
        if path.startswith(allowed_dir):
            return True
    return False


# MCP Tools
async def read_file(path: str) -> bytes:
    """
    Read a file from the file system
    """
    # Check if the path is valid
    pass

async def read_mutliple_files(paths: list) -> list:
    """
    Read multiple files from the file system
    """
    # Check if the paths are valid
    pass

async def write_file(path: str, data: bytes) -> None:
    pass

async def move_file(src: str, dest: str) -> None:
    pass

async def delete_file(path: str) -> None:
    pass

async def list_files(path: str) -> list:
    """
    List files in a directory
    """
    # Check if the path is valid
    pass

async def create_directory(path: str) -> None:
    pass

