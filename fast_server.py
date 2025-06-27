from fastmcp import FastMCP
import httpx
from config import TOKEN,BASE_URL
from utils.auth import SimpleBearerAuthProvider
from tools.core_tools import register_core_tools
from tools.extra_tools import register_extra_tools
from tools.calender_tools import register_calendar_tools

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow
import os
import json

TOKEN_DIR = "tokens"
STATE_DIR = "states"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
os.makedirs(TOKEN_DIR, exist_ok=True)
os.makedirs(STATE_DIR, exist_ok=True)

# # --- Create MCP + underlying FastAPI app ---
# app = FastAPI()
# mcp = FastMCP("My MCP Server", auth=SimpleBearerAuthProvider(TOKEN), stateless_http=True)
# mcp.from_fastapi(app)

# Create unified FastAPI app
# MCP core
app = FastAPI()


FASTMCP_URL = "http://localhost:8085/mcp"  # Assuming FastMCP runs here

@app.api_route("/mcp/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_fastmcp(request: Request, path: str):
    # Construct the full target URL
    target_url = f"{FASTMCP_URL}/{path}"
    
    # Extract original request data
    method = request.method
    headers = dict(request.headers)
    body = await request.body()
    query_params = dict(request.query_params)

    # Make the proxied request
    async with httpx.AsyncClient() as client:
        proxy_response = await client.request(
            method=method,
            url=target_url,
            headers=headers,
            content=body,
            params=query_params
        )

    # Return raw response from FastMCP
    return Response(
        content=proxy_response.content,
        status_code=proxy_response.status_code,
        headers=dict(proxy_response.headers),
        media_type=proxy_response.headers.get("content-type", "application/json")
    )



# --- OAuth endpoints ---

@app.get("/oauth/initiate")
def initiate_oauth(user_id: str):
    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri=f"{BASE_URL}/oauth/callback"
    )
    auth_url, state = flow.authorization_url(prompt="consent", access_type='offline', include_granted_scopes='true')
    with open(f"{STATE_DIR}/{state}.json", "w") as f:
        json.dump({"user_id": user_id}, f)
    return {"auth_url": auth_url}

@app.get("/oauth/callback")
def oauth_callback(request: Request):
    state = request.query_params["state"]
    code = request.query_params["code"]
    state_file = f"{STATE_DIR}/{state}.json"

    if not os.path.exists(state_file):
        return HTMLResponse("Invalid or expired state. Please restart the process.", status_code=400)

    with open(state_file, "r") as f:
        user_id = json.load(f)["user_id"]

    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri=f"{BASE_URL}/oauth/callback"
    )
    flow.fetch_token(code=code)
    creds = flow.credentials

    with open(f"{TOKEN_DIR}/{user_id}.json", "w") as token_file:
        token_file.write(creds.to_json())

    return HTMLResponse(f"<h2>✅ Calendar connected for {user_id}</h2><p>You can now go back to WhatsApp and use calendar tools.</p>")

# --- Run everything ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
