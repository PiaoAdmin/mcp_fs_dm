import sys
sys.path.append("/Users/tangbingbing/workspace/mcp/mcp_fs_dm")  # Add the parent directory to the path

import asyncio

from server.src.config import ConfigManager
from server.src.tools.file_system import is_path_allowed, normalize_path


def test_demo():
    ConfigManager("/home/piao/workspace/mcp/mcp-data-manager/server/src/config.json")
    return asyncio.run(is_path_allowed("~/workspace"))

if __name__ == '__main__':
    print(test_demo())
    print(normalize_path("~/workspace"))
    print(normalize_path("/home/piao/workspace/../mcp/mcp-data-manager/server/src/config.json"))
    print(normalize_path(""))