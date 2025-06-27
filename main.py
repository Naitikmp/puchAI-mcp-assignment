from fastmcp import FastMCP
from config import TOKEN
from utils.auth import SimpleBearerAuthProvider
from tools.core_tools import register_core_tools
from tools.extra_tools import register_extra_tools
from tools.calender_tools import register_calendar_tools

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow
import os
import json

# TOKEN_DIR = "tokens"
# STATE_DIR = "states"
# SCOPES = ["https://www.googleapis.com/auth/calendar"]
# os.makedirs(TOKEN_DIR, exist_ok=True)
# os.makedirs(STATE_DIR, exist_ok=True)

# # --- Create MCP + underlying FastAPI app ---
# app = FastAPI()
# mcp = FastMCP("My MCP Server", auth=SimpleBearerAuthProvider(TOKEN), stateless_http=True)
# mcp.from_fastapi(app)

# Create unified FastAPI app
# MCP core
# app = FastAPI()
mcp = FastMCP("My MCP Server", auth=SimpleBearerAuthProvider(TOKEN), stateless_http=True)
# app = mcp
# --- Register MCP tools ---
register_core_tools(mcp)
register_extra_tools(mcp)
register_calendar_tools(mcp)


# @app.post("/")
# async def mcp_handler(request: Request):
#     body = await request.body()
#     headers = dict(request.headers)

#     try:
#         request_json = json.loads(body.decode("utf-8"))
#     except Exception as e:
#         return JSONResponse({"error": f"Invalid JSON: {e}"}, status_code=400)

#     response = await mcp.call_json(request_json, headers=headers)

#     return JSONResponse(content=response)

# # --- OAuth endpoints ---

# @app.get("/oauth/initiate")
# def initiate_oauth(user_id: str):
#     flow = Flow.from_client_secrets_file(
#         "credentials.json",
#         scopes=SCOPES,
#         redirect_uri="https://53a5-182-68-21-186.ngrok-free.app/oauth/callback"
#     )
#     auth_url, state = flow.authorization_url(prompt="consent", access_type='offline', include_granted_scopes='true')
#     with open(f"{STATE_DIR}/{state}.json", "w") as f:
#         json.dump({"user_id": user_id}, f)
#     return {"auth_url": auth_url}

# @app.get("/oauth/callback")
# def oauth_callback(request: Request):
#     state = request.query_params["state"]
#     code = request.query_params["code"]
#     state_file = f"{STATE_DIR}/{state}.json"

#     if not os.path.exists(state_file):
#         return HTMLResponse("Invalid or expired state. Please restart the process.", status_code=400)

#     with open(state_file, "r") as f:
#         user_id = json.load(f)["user_id"]

#     flow = Flow.from_client_secrets_file(
#         "credentials.json",
#         scopes=SCOPES,
#         redirect_uri="https://53a5-182-68-21-186.ngrok-free.app/oauth/callback"
#     )
#     flow.fetch_token(code=code)
#     creds = flow.credentials

#     with open(f"{TOKEN_DIR}/{user_id}.json", "w") as token_file:
#         token_file.write(creds.to_json())

#     return HTMLResponse(f"<h2>✅ Calendar connected for {user_id}</h2><p>You can now go back to WhatsApp and use calendar tools.</p>")

# --- Run everything ---
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8085)


if __name__ == "__main__":
    import asyncio
    async def main():
        await mcp.run_async("http", host="0.0.0.0", port=8085)
    asyncio.run(main())