import argparse
from typing_extensions import Literal
from mcp.server.fastmcp import FastMCP
from server.tools.file_system import read_file, write_file, delete_file, list_files, move_file, create_directory, FileResult
from server.config import get_config_manager


mcp_server = FastMCP(
    "file_system",
    description="A file system data manager for MCP",
    version="0.1.0",
)


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