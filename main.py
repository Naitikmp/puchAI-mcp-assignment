from fastmcp import FastMCP
from config import TOKEN
from utils.auth import SimpleBearerAuthProvider
from tools.core_tools import register_core_tools
from tools.extra_tools import register_extra_tools
from tools.calender_tools import register_calendar_tools
from tools.stock_market_tools import register_stock_market_tools
from tools.train_tools import register_railway_tools
from tools.vehicle_tools import register_vehicle_tools
from tools.parcel_tracker_tools import register_parcel_tracker_tools
from tools.map_tools import register_map_services_tools
from tools.ascii_art_tools import register_ascii_art_tools
from tools.flight_tools import register_flight_tools

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow
import os
import json

mcp = FastMCP("My MCP Server", auth=SimpleBearerAuthProvider(TOKEN), stateless_http=True)

# --- Register MCP tools ---
register_core_tools(mcp)
register_extra_tools(mcp)
register_calendar_tools(mcp)
register_stock_market_tools(mcp)
register_railway_tools(mcp)
register_vehicle_tools(mcp)
register_parcel_tracker_tools(mcp)
register_map_services_tools(mcp)
register_ascii_art_tools(mcp)
register_flight_tools(mcp)

if __name__ == "__main__":
    import asyncio
    async def main():
        await mcp.run_async("http", host="0.0.0.0", port=8085)
    asyncio.run(main())