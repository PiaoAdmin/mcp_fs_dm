import asyncio

from server.src.config import ConfigManager
from server.src.tools.file_system import is_path_allowed

def test_demo():
    ConfigManager("/home/piao/workspace/mcp/mcp-data-manager/server/src/config.json")
    return asyncio.run(is_path_allowed("~/workspace"))

if __name__ == '__main__':
    print(test_demo())