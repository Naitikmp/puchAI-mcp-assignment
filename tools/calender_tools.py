# # calendar_tools.py

# import os
# import datetime
# from config import BASE_URL
# from google.oauth2.credentials import Credentials
# from googleapiclient.discovery import build
# from mcp import McpError, ErrorData
# from mcp.types import TextContent
# from openai import BaseModel
# import requests

# SCOPES = ["https://www.googleapis.com/auth/calendar"]
# TOKEN_DIR = "tokens"
# os.makedirs(TOKEN_DIR, exist_ok=True)

# def get_user_calendar_service(user_id: str):
#     token_path = os.path.join(TOKEN_DIR, f"{user_id}.json")
#     if not os.path.exists(token_path):
#         raise McpError(ErrorData(code=401, message="User not authenticated. Send 'Connect calendar' first."))
#     creds = Credentials.from_authorized_user_file(token_path, SCOPES)
#     return build("calendar", "v3", credentials=creds)

# def register_calendar_tools(mcp):
#     class RichToolDescription(BaseModel):
#         description: str
#         use_when: str
#         side_effects: str | None

#     CalendarConnectToolDesc = RichToolDescription(
#         description="Connect the user's Google Calendar using OAuth.",
#         use_when="user asks for connecting to calendar",
#         side_effects="Returns a link to connect calendar"
#     )

#     @mcp.tool(description=CalendarConnectToolDesc.model_dump_json())
#     async def connect_calendar(user_id: str) -> str:
#         # Hit your FastAPI endpoint to get auth_url
#         response = requests.get(f"{BASE_URL}/oauth/initiate", params={"user_id": user_id})
#         if response.status_code == 200:
#             auth_url = response.json()["auth_url"]
#             return f"🔗 Click to connect your calendar: {auth_url}"
#         else:
#             return "❌ Failed to initiate calendar connection. Try again later."


#     CalendarAddEventToolDesc = RichToolDescription(
#             description="Schedule an event on the user's Google Calendar.",
#             use_when="user asks to add or edit an event",
#             side_effects="Updates the google calendar with the new event"
#         )
#     @mcp.tool(description=CalendarAddEventToolDesc.model_dump_json())
#     async def add_event_for_user(user_id: str, title: str, start_time: str, end_time: str) -> str:
#         try:
#             service = get_user_calendar_service(user_id)
#             event = {
#                 'summary': title,
#                 'start': {'dateTime': start_time, 'timeZone': 'Asia/Kolkata'},
#                 'end': {'dateTime': end_time, 'timeZone': 'Asia/Kolkata'},
#             }
#             created_event = service.events().insert(calendarId='primary', body=event).execute()
#             return f"✅ Event '{title}' created for {start_time}"
#         except Exception as e:
#             raise McpError(ErrorData(code=1, message=f"Failed to create event: {e}"))

#     CalendarListEventsToolDesc = RichToolDescription(
#         description = "List next 5 events for a user from Google Calendar.",
#         use_when = "user asks for upcoming events",
#         side_effects = "Fetches events from the user's Google Calendar"
#     )
#     @mcp.tool(description=CalendarListEventsToolDesc.model_dump_json())
#     async def list_upcoming_events(user_id: str) -> list[TextContent]:
#         try:
#             service = get_user_calendar_service(user_id)
#             now = datetime.datetime.utcnow().isoformat() + 'Z'
#             events_result = service.events().list(calendarId='primary', timeMin=now,
#                                                   maxResults=5, singleEvents=True,
#                                                   orderBy='startTime').execute()
#             events = events_result.get('items', [])
#             if not events:
#                 return [TextContent(type="text", text="No upcoming events found.")]
#             output = [f"- {e['summary']} at {e['start'].get('dateTime', e['start'].get('date'))}" for e in events]
#             return [TextContent(type="text", text="\n".join(output))]
#         except Exception as e:
#             raise McpError(ErrorData(code=1, message=f"Failed to fetch events: {e}"))
# calendar_tools.py

import os
import datetime
from config import BASE_URL
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from mcp import McpError, ErrorData
from mcp.types import TextContent
from openai import BaseModel
import requests

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
    class RichToolDescription(BaseModel):
        description: str
        use_when: str
        side_effects: str | None

    CalendarConnectToolDesc = RichToolDescription(
        description="Connect the user's Google Calendar using OAuth.",
        use_when="user asks for connecting to calendar",
        side_effects="Returns a link to connect calendar"
    )

    @mcp.tool(description=CalendarConnectToolDesc.model_dump_json())
    async def connect_calendar(user_id: str) -> str:
        # Hit your FastAPI endpoint to get auth_url
        response = requests.get(f"{BASE_URL}/oauth/initiate", params={"user_id": user_id})
        if response.status_code == 200:
            auth_url = response.json()["auth_url"]
            return f"🔗 Click to connect your calendar: {auth_url}"
        else:
            return "❌ Failed to initiate calendar connection. Try again later."

    CalendarAddEventToolDesc = RichToolDescription(
        description="Schedule an event on the user's Google Calendar with optional Google Meet link.",
        use_when="user asks to add, schedule, or create an event, meeting, or appointment",
        side_effects="Creates a new event in Google Calendar, optionally with Google Meet video conference"
    )
    
    @mcp.tool(description=CalendarAddEventToolDesc.model_dump_json())
    async def add_event_for_user(
        user_id: str, 
        title: str, 
        start_time: str, 
        end_time: str, 
        description: str = "", 
        include_meet: bool = False,
        attendees: list[str] = None
    ) -> str:
        try:
            service = get_user_calendar_service(user_id)
            
            # Base event structure
            event = {
                'summary': title,
                'start': {'dateTime': start_time, 'timeZone': 'Asia/Kolkata'},
                'end': {'dateTime': end_time, 'timeZone': 'Asia/Kolkata'},
            }
            
            # Add description if provided
            if description:
                event['description'] = description
            
            # Add attendees if provided
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            # Add Google Meet if requested
            if include_meet:
                event['conferenceData'] = {
                    'createRequest': {
                        'requestId': f"meet-{user_id}-{int(datetime.datetime.now().timestamp())}",
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                }
                # Send notifications when Meet is included
                event['guestsCanInviteOthers'] = False
                event['guestsCanModify'] = False
                event['guestsCanSeeOtherGuests'] = True
            
            # Create the event
            created_event = service.events().insert(
                calendarId='primary', 
                body=event,
                conferenceDataVersion=1 if include_meet else 0,
                sendUpdates='all' if attendees else 'none'
            ).execute()
            
            # Format response
            response_text = f"✅ Event '{title}' created for {start_time}"
            
            if include_meet and 'conferenceData' in created_event:
                meet_link = created_event['conferenceData']['entryPoints'][0]['uri']
                response_text += f"\n🎥 Google Meet: {meet_link}"
            
            if attendees:
                response_text += f"\n📧 Invitations sent to: {', '.join(attendees)}"
                
            return response_text
            
        except Exception as e:
            raise McpError(ErrorData(code=1, message=f"Failed to create event: {e}"))

    # New tool specifically for Google Meet meetings
    CalendarAddMeetingToolDesc = RichToolDescription(
        description="Schedule a Google Meet video conference with automatic meet link generation.",
        use_when="user specifically asks to schedule a Google Meet, video call, or online meeting",
        side_effects="Creates a calendar event with Google Meet link and sends invitations to attendees"
    )
    
    @mcp.tool(description=CalendarAddMeetingToolDesc.model_dump_json())
    async def schedule_google_meet(
        user_id: str,
        title: str,
        start_time: str,
        end_time: str,
        attendees: list[str],
        agenda: str = ""
    ) -> str:
        """Schedule a Google Meet with attendees"""
        try:
            service = get_user_calendar_service(user_id)
            
            # Prepare description with agenda
            description = f"Google Meet Video Conference\n\n"
            if agenda:
                description += f"Agenda:\n{agenda}\n\n"
            description += "Join the meeting using the link above."
            
            event = {
                'summary': title,
                'description': description,
                'start': {'dateTime': start_time, 'timeZone': 'Asia/Kolkata'},
                'end': {'dateTime': end_time, 'timeZone': 'Asia/Kolkata'},
                'attendees': [{'email': email} for email in attendees],
                'conferenceData': {
                    'createRequest': {
                        'requestId': f"meet-{user_id}-{int(datetime.datetime.now().timestamp())}",
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                },
                'guestsCanInviteOthers': False,
                'guestsCanModify': False,
                'guestsCanSeeOtherGuests': True,
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 10},
                        {'method': 'email', 'minutes': 1440}  # 24 hours
                    ]
                }
            }
            
            created_event = service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1,
                sendUpdates='all'
            ).execute()
            
            # Extract meet link
            meet_link = "Meet link will be generated"
            if 'conferenceData' in created_event and 'entryPoints' in created_event['conferenceData']:
                meet_link = created_event['conferenceData']['entryPoints'][0]['uri']
            
            response = f"🎥 Google Meet '{title}' scheduled for {start_time}\n"
            response += f"📅 Event ID: {created_event['id']}\n"
            response += f"🔗 Meet Link: {meet_link}\n"
            response += f"📧 Invitations sent to: {', '.join(attendees)}"
            
            return response
            
        except Exception as e:
            raise McpError(ErrorData(code=1, message=f"Failed to schedule Google Meet: {e}"))

    CalendarListEventsToolDesc = RichToolDescription(
        description="List next 5 events for a user from Google Calendar with meet links if available.",
        use_when="user asks for upcoming events, schedule, or agenda",
        side_effects="Fetches events from the user's Google Calendar"
    )
    
    @mcp.tool(description=CalendarListEventsToolDesc.model_dump_json())
    async def list_upcoming_events(user_id: str) -> list[TextContent]:
        try:
            service = get_user_calendar_service(user_id)
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = service.events().list(
                calendarId='primary', 
                timeMin=now,
                maxResults=5, 
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            if not events:
                return [TextContent(type="text", text="📅 No upcoming events found.")]
            
            output_lines = ["📅 **Upcoming Events:**\n"]
            
            for i, event in enumerate(events, 1):
                start_time = event['start'].get('dateTime', event['start'].get('date'))
                line = f"{i}. **{event['summary']}**\n   📅 {start_time}"
                
                # Add meet link if available
                if 'conferenceData' in event and 'entryPoints' in event['conferenceData']:
                    meet_link = event['conferenceData']['entryPoints'][0]['uri']
                    line += f"\n   🎥 [Join Meet]({meet_link})"
                
                # Add location if available
                if event.get('location'):
                    line += f"\n   📍 {event['location']}"
                    
                output_lines.append(line)
            
            return [TextContent(type="text", text="\n\n".join(output_lines))]
            
        except Exception as e:
            raise McpError(ErrorData(code=1, message=f"Failed to fetch events: {e}"))