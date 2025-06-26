from fastmcp import FastMCP
from config import TOKEN
from utils.auth import SimpleBearerAuthProvider

mcp = FastMCP("My MCP Server", auth=SimpleBearerAuthProvider(TOKEN),stateless_http=True)
# from tools.core_tools import resume, validate, fetch
# from tools.extra_tools import weather, web_search

from tools.core_tools import register_core_tools
from tools.extra_tools import register_extra_tools
# from tools.extra_tools

register_core_tools(mcp)
register_extra_tools(mcp)

if __name__ == "__main__":
    import asyncio
    async def main():
        await mcp.run_async("http", host="0.0.0.0", port=8085)
    asyncio.run(main())
