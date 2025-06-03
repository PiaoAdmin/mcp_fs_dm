import base64
from dataclasses import dataclass
import logging
import os
from typing import Literal
from server.config import get_config_manager
from server.tools.mime_types import get_mime_type,is_image_file
from server.utils.execute_with_timeout import execute_with_timeout


def normalize_path(path: str) -> str:
    """
    Normalize the path by expanding user directory and removing trailing separators

    :param path: The path to normalize
    :return: The normalized path
    """
    if not path:
        raise ValueError("Path is empty")
    if path.startswith("~") or path == '~':
        # Expand the home directory
        path = os.path.expanduser(path)
    path = os.path.abspath(path)
    path = os.path.normpath(path)
    return path.rstrip(os.sep)


def get_allowed_dirs() -> list:
    """
    Get the allowed directories from configuration
    """
    try:
        config = get_config_manager()
        allowed_dirs = config.config.get("allowed_directories", [])
        # If no allowed dirs are set, use the home directory
        if not allowed_dirs:
            allowed_dirs = [os.environ['HOME']]
            config.set_value("allowed_directories", allowed_dirs)
        allowed_dirs = [normalize_path(p) for p in allowed_dirs]
        return allowed_dirs
    except Exception as e:
        logging.error(f"Error getting allowed dirs:{e}")
    return []


def is_path_allowed(path: str) -> bool:
    """
    Check if the path is allowed to access

    :param path: The path to check
    :return: True if the path is allowed, False otherwise
    """
    allowed_dirs = get_allowed_dirs()
    if "/" in allowed_dirs or not allowed_dirs:
        # If the allowed dirs are empty or contain "/", allow all paths
        return True
    path = normalize_path(path)
    for allowed_dir in allowed_dirs:
        if path == allowed_dir or path.startswith(allowed_dir + os.sep):
            # If the path is the same as the allowed dir or starts with it, allow it
            return True
    return False


def validate_parent_dirs(path: str) -> bool:
    """
    Recursively validates parent directories until it finds a valid one

    :param path: The path to validate
    :return: True  the parent directory exists, False otherwise
    """
    parent = os.path.dirname(path)
    if parent == path or parent == os.path.dirname(parent):
        return False
    if os.path.exists(parent):
        return True
    return validate_parent_dirs(parent)


def is_path_valid(path: str) -> bool:
    """
    Check if the path is valid

    :param path: The path to check
    :return: True if the path is valid, False otherwise
    """
    # Check if the path 
    if not validate_parent_dirs(path):
        return False
    # Check if the path is allowed
    if not is_path_allowed(path):
        return False
    return True


# MCP Tools
@dataclass
class FileResult:
    """
    File result class
    """
    file_content: str
    file_path: str
    mini_type: str
    is_image: bool


def read_file_from_disk(path: str, offset: int = 0, length: int = None, read_all: bool = None) -> FileResult:
    """
    Read a file from the disk

    :param path: The path to the file
    :param offset: Offset Starting line number to read from (default: 0)
    :param length: Length Maximum number of lines to read (default: from config or 1000)
    :param read_all: If True, read the entire file, otherwise read from offset to length
    :return: FileResult containing the file content, path, mime type, and whether it is an image
    """
    if not path:
        raise ValueError("Path is empty")

    path = normalize_path(path)
    if not is_path_valid(path):
        logging.error(f"Path is not valid: {path}")
        raise ValueError(f"Path is not valid: {path}")

    if not os.path.exists(path):
        logging.error(f"Path does not exist: {path}")
        raise FileNotFoundError(f"Path does not exist: {path}")

    if offset < 0:
        raise ValueError("Offset must be greater than or equal to 0")

    if length is None and read_all is None:
        config = get_config_manager()
        length = config.config.get("max_read_length", 1000)

    mime_type = get_mime_type(path)
    is_image = is_image_file(mime_type)

    #TODO: 可以使用配置文件
    FILE_READ_TIMEOUT = 10  # seconds
    def read_operation() -> str:
        try:
            if is_image:
                # For images, we read full content and encode it in base64
                with open(path, 'rb') as f:
                    content = f.read()
                return base64.b64encode(content).decode('utf-8')
            else:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        if read_all:
                            content = f.read()
                        else:
                            lines = f.readlines()
                            if offset >= len(lines):
                                return ""
                            end_ind = min(offset + length, len(lines))
                            selected_lines = lines[offset:end_ind]
                            content = ''.join(selected_lines)
                        return content
                except UnicodeDecodeError:
                    # If the file is not a text file, read it as binary
                    # Ignore offset and length
                    with open(path, 'rb') as f:
                        content = f.read()
                    return base64.b64encode(content).decode('utf-8')
        except Exception as e:
            logging.error(f"Error reading file {path}: {e}")
            raise e

    executed_content = execute_with_timeout(read_operation, timeout=FILE_READ_TIMEOUT, default_value="")

    return FileResult(
        file_content=executed_content,
        file_path=path,
        mini_type=mime_type,
        is_image=is_image
    )


def read_file(path: str, offset: int = 0, length: int = None, read_all: bool = None) -> FileResult:
    return read_file_from_disk(path, offset, length, read_all)
    

def write_file(path: str, content: str,  mode: Literal["rewrite", "append"] = 'rewrite') -> None:
    """
    Write content to a file

    :param path: The path to the file
    :param content: The content to write to the file
    :param mode: The mode to write the file, either 'rewrite' or 'append'
    """
    if not path:
        raise ValueError("Path is empty")

    path = normalize_path(path)
    if not is_path_valid(path):
        logging.error(f"Path is not valid: {path}")
        raise ValueError(f"Path is not valid: {path}")

    write_mode = 'w' if mode == 'rewrite' else 'a'

    FILE_WRITE_TIMEOUT = 30  # seconds
    def write_operation() -> None:
        try:
            with open(path, write_mode, encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logging.error(f"Error writing file {path}: {e}")
            raise e

    execute_with_timeout(
        write_operation,
        timeout=FILE_WRITE_TIMEOUT,
        default_value=None
    )


def move_file(src: str, dest: str) -> None:
    """
    Move a file from src to dest, if the destination exists, it will be overwritten

    :param src: The source path of the file
    :param dest: The destination path of the file
    """
    if not src or not dest:
        raise ValueError("Source or destination path is empty")

    src = normalize_path(src)
    dest = normalize_path(dest)
    if not is_path_valid(src) or not is_path_valid(dest):
        logging.error(f"Source or destination path is not valid: {src} -> {dest}")
        raise ValueError(f"Source or destination path is not valid: {src} -> {dest}")

    if not os.path.exists(src):
        logging.error(f"Source path does not exist: {src}")
        raise FileNotFoundError(f"Source path does not exist: {src}")

    def move_operation() -> None:
        try:
            dest_dir = os.path.dirname(dest)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

            os.rename(src, dest)

        except Exception as e:
            logging.error(f"Error moving file from {src} to {dest}: {e}")
            raise e

    FILE_MOVE_TIMEOUT = 30  # seconds
    execute_with_timeout(
        move_operation,
        timeout=FILE_MOVE_TIMEOUT,
        default_value=None
    )


def delete_file(path: str) -> None:
    """
    Delete a file

    :param path: The path to the file
    """
    if not path:
        raise ValueError("Path is empty")
    path = normalize_path(path)
    if not is_path_valid(path):
        logging.error(f"Path is not valid: {path}")
        raise ValueError(f"Path is not valid: {path}")
    if not os.path.exists(path):
        logging.error(f"Path does not exist: {path}")
        raise FileNotFoundError(f"Path does not exist: {path}")
    def delete_operation() -> None:
        try:
            os.remove(path)
        except Exception as e:
            logging.error(f"Error deleting file {path}: {e}")
            raise e
    FILE_DELETE_TIMEOUT = 10  # seconds
    execute_with_timeout(
        delete_operation,
        timeout=FILE_DELETE_TIMEOUT,
        default_value=None
    )


def list_files(path: str) -> list:
    """
    List files in a directory

    :param path: The directory path to list
    :return: List of file and directory information
    """
    if not path:
        raise ValueError("Path is empty")
    path = normalize_path(path)
    if not is_path_valid(path):
        logging.error(f"Path is not valid: {path}")
        raise ValueError(f"Path is not valid: {path}")
    if not os.path.exists(path):
        logging.error(f"Path does not exist: {path}")
        raise FileNotFoundError(f"Path does not exist: {path}")
    if not os.path.isdir(path):
        raise ValueError(f"Path is not a directory: {path}")
    def list_operation():
        try:
            items = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                item_stat = os.stat(item_path)
                items.append({
                    'name': item,
                    'path': item_path,
                    'is_directory': os.path.isdir(item_path),
                    'size': item_stat.st_size,
                    'modified': item_stat.st_mtime
                })
            return items
        except Exception as e:
            logging.error(f"Error listing directory {path}: {e}")
            raise e

    FILE_LIST_TIMEOUT = 10  # seconds
    return execute_with_timeout(
        list_operation,
        timeout=FILE_LIST_TIMEOUT,
        default_value=[]
    )


def create_directory(path: str) -> None:
    """
    Create a directory

    :param path: The directory path to create
    """
    if not path:
        raise ValueError("Path is empty")
    path = normalize_path(path)
    if not is_path_valid(path):
        logging.error(f"Path is not valid: {path}")
        raise ValueError(f"Path is not valid: {path}")

    def create_operation():
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            logging.error(f"Error creating directory {path}: {e}")
            raise e

    FILE_CREATE_TIMEOUT = 10  # seconds
    execute_with_timeout(
        create_operation,
        timeout=FILE_CREATE_TIMEOUT,
        default_value=None
    )

