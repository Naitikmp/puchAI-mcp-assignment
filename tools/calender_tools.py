# calendar_tools.py

import os
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from mcp import McpError, ErrorData
from mcp.types import TextContent

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_DIR = "tokens"
os.makedirs(TOKEN_DIR, exist_ok=True)

def get_user_calendar_service(user_id: str):
    token_path = os.path.join(TOKEN_DIR, f"{user_id}.json")
    if not os.path.exists(token_path):
        raise McpError(ErrorData(code=401, message="User not authenticated. Send 'Connect calendar' first."))
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    return build("calendar", "v3", credentials=creds)

def register_calendar_tools(mcp):
    @mcp.tool(description="Schedule an event on the user's Google Calendar.")
    async def add_event_for_user(user_id: str, title: str, start_time: str, end_time: str) -> str:
        try:
            service = get_user_calendar_service(user_id)
            event = {
                'summary': title,
                'start': {'dateTime': start_time, 'timeZone': 'Asia/Kolkata'},
                'end': {'dateTime': end_time, 'timeZone': 'Asia/Kolkata'},
            }
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            return f"✅ Event '{title}' created for {start_time}"
        except Exception as e:
            raise McpError(ErrorData(code=1, message=f"Failed to create event: {e}"))

    @mcp.tool(description="List next 5 events for a user from Google Calendar.")
    async def list_upcoming_events(user_id: str) -> list[TextContent]:
        try:
            service = get_user_calendar_service(user_id)
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = service.events().list(calendarId='primary', timeMin=now,
                                                  maxResults=5, singleEvents=True,
                                                  orderBy='startTime').execute()
            events = events_result.get('items', [])
            if not events:
                return [TextContent(type="text", text="No upcoming events found.")]
            output = [f"- {e['summary']} at {e['start'].get('dateTime', e['start'].get('date'))}" for e in events]
            return [TextContent(type="text", text="\n".join(output))]
        except Exception as e:
            raise McpError(ErrorData(code=1, message=f"Failed to fetch events: {e}"))