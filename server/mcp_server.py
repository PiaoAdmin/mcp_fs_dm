import sys
from pathlib import Path

project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

import argparse
from typing_extensions import Literal
from mcp.server.fastmcp import FastMCP
from server.tools.file_system import read_file, write_file, delete_file, list_files, move_file, create_directory, FileResult
from server.config import get_config_manager
from server.tools.commands import execute_command, read_output, get_active_sessions, force_terminate

mcp_server = FastMCP(
    "file_system",
    description="A file system data manager for MCP",
    version="0.1.0",
)

# File system tools
@mcp_server.tool()
def read_file_tool(path: str, offset: int = 0, length: int = None, read_all: bool = None) -> FileResult:
    """
    Read a file and return its content.
    
    :param path: The path to the file to read.
    :param offset: The offset from which to start reading.
    :param length: Length Maximum number of lines to read (default: from config or 1000).
    :param read_all: If True, read the entire file, otherwise read from offset to length
    :return: FileResult containing the file content, path, mime type, and whether it is an image.
    """
    return read_file(path, offset, length, read_all)


@mcp_server.tool()
def write_file_tool(file_path: str, content: str, mode: Literal["rewrite", "append"] = 'rewrite') -> bool:
    """
    Write content to a file.
    
    :param file_path: The path to the file to write to.
    :param content: The content to write to the file.
    :param mode: The mode in which to write the file ('rewrite' or 'append').
    :return: True if the file was written successfully, False otherwise.
    """
    return True if write_file(file_path, content, mode) is None else False


@mcp_server.tool()
def move_file_tool(source: str, destination: str) -> bool:
    """
    Move a file from source to destination.
    
    :param source: The path to the source file.
    :param destination: The path to the destination file.
    :return: True if the file was moved successfully, False otherwise.
    """
    return True if move_file(source, destination) is None else False


@mcp_server.tool()
def delete_file_tool(file_path: str) -> bool:
    """
    Delete a file.
    
    :param file_path: The path to the file to delete.
    :return: True if the file was deleted successfully, False otherwise.
    """
    return True if delete_file(file_path) is None else False


@mcp_server.tool()
def list_files_tool(directory: str) -> list:
    """
    List files in a directory.
    
    :param directory: The path to the directory to list files from.
    :return: A list of file names in the directory.
    """
    return list_files(directory)


@mcp_server.tool()
def create_directory_tool(directory: str) -> bool:
    """
    Create a directory.
    
    :param directory: The path to the directory to create.
    :return: True if the directory was created successfully, False otherwise.
    """
    return True if create_directory(directory) is None else False


# Configuration management tools
@mcp_server.tool()
def get_config_tool() -> dict:
    """
    Get the current configuration.
    """
    config_manager = get_config_manager()
    return config_manager.config


@mcp_server.tool()
def set_config_tool(key: str, value) -> dict:
    """
    Set a configuration value.
    
    :param key: The configuration key to set.
    :param value: The value to set for the configuration key.
    :return: The updated configuration.
    """
    config_manager = get_config_manager()
    config_manager.set_value(key, value)
    return config_manager.config


# Command execution tools
@mcp_server.tool()
def execute_command_tool(command: str, timeout: float, shell: str = None) -> dict:
    """
    Execute a command in the shell.
    
    :param command: The command to execute.
    :param timeout: The timeout for the command execution.
    :param shell: The shell to use for execution, optional.
    :return: A dict containing the result of the command execution.
    """
    return execute_command(command, timeout=timeout, shell=shell)


@mcp_server.tool()
def read_output_tool(pid: int, is_full: bool = False) -> dict:
    """
    Read the output of a command execution.
    
    :param pid: The process ID of the command.
    :param is_full: Whether to read the full output or just the new output.
    :return: A dict containing the output of the command.
    """
    return read_output(pid, is_full)


@mcp_server.tool()
def get_active_sessions_tool() -> dict:
    """
    Get the list of active command execution sessions.
    
    :return: A dict containing the active sessions and their details.
    """
    return get_active_sessions()


@mcp_server.tool()
def force_terminate_tool(pid: int) -> dict:
    """
    Force terminate a command execution session.
    
    :param pid: The process ID of the command to terminate.
    :return: A dict indicating whether the termination was successful.
    """
    return force_terminate(pid)


def main():
    """
    Main entry point for the server.
    """
    parser = argparse.ArgumentParser(description="Run the server with custom config.")
    parser.add_argument("--config", help="Path to config file", default=None)
    args = parser.parse_args()
    get_config_manager(config_path=args.config)
    mcp_server.run(transport='stdio')


if __name__ == "__main__":
    main()