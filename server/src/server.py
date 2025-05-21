from mcp.server.fastmcp import FastMCP
import pandas as pd
import numpy as np
from mcp.server.fastmcp.resources import types

mcp = FastMCP(
    "data_manager",
)


@mcp.resource(uri="config://app",name="config")
async def get_config() -> str:
    """Static configuration data"""
    return "App configuration here"

@mcp.resource("users://{user_id}/profile")
async def get_user_profile(user_id: str) -> str:
    """Dynamic user data"""
    return f"Profile data for user {user_id}"

@mcp.resource("file://{path}")
async def get_data(path: str):
    """
    Get data from the data manager
    """
    data = None
    file_type = path.split(".")[-1]
    if file_type == "csv":
        # data = pd.read_csv(path)
        return "这是一个csv"
    elif file_type == "json":
        # data = pd.read_json(path)
        return "这是一个json"
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    # return data

@mcp.tool()
async def hello_world(name: str):
    """
    Return a hello world message
    """
    return f"Hello {name}!"

@mcp.tool()
async def get_iris(name: str):
    """
    Get the dataset of iris
    """
    return f"Hello {name}!"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')