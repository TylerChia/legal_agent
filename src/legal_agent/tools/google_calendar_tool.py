# src/legal_agent/tools/simple_calendar_tool.py
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import pytz
import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar']

class CalendarEventInput(BaseModel):
    """Input schema for Google Calendar event creation."""
    summary: str = Field(..., description="Title of the calendar event")
    description: str = Field(..., description="Description of the event")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    user_email: str = Field(..., description="Email address to invite to the event")

class SimpleGoogleCalendarTool(BaseTool):
    name: str = "Google Calendar Tool"
    description: str = "Creates Google Calendar events for contract deliverables and invites users via email."
    args_schema: Type[BaseModel] = CalendarEventInput

    def _run(self, summary: str, description: str, start_date: str, user_email: str) -> str:
        """Create a Google Calendar event using token from environment variable."""
        try:
            # Get token from environment variable
            token_json = json.loads(os.getenv('GOOGLE_CALENDAR_TOKEN_JSON'))
            if not token_json:
                return "❌ Google Calendar not set up. GOOGLE_CALENDAR_TOKEN_JSON environment variable not found."
            
            try:
                # Parse the token JSON from environment variable
                token_data = token_json
                creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            except json.JSONDecodeError:
                return "❌ Invalid token format in GOOGLE_CALENDAR_TOKEN_JSON. Must be valid JSON."
            except Exception as e:
                return f"❌ Failed to load credentials from environment variable: {str(e)}"
            
            # Check if token is valid and refresh if needed
            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        # Note: We can't update the env variable, but we can use the refreshed token for this session
                        print("🔄 Token refreshed successfully")
                    except Exception as e:
                        return f"❌ Token expired and could not be refreshed: {str(e)}"
                else:
                    return "❌ Invalid token. Please update the GOOGLE_CALENDAR_TOKEN_JSON environment variable."
            
            service = build('calendar', 'v3', credentials=creds)
            
            # Parse the date and set to 9 AM PST
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            pst = pytz.timezone('America/Los_Angeles')
            start_dt = pst.localize(start_dt)
            
            end_dt = start_dt + timedelta(hours=1)  # 1-hour event

            # --- 🧠 Duplicate check ---
            time_min = start_dt.isoformat()
            time_max = (start_dt + timedelta(days=1)).isoformat()
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])

            for e in events:
                existing_summary = e.get('summary', '').strip().lower()
                if existing_summary == f"📋 {summary}".lower():
                    print(f"Duplicate event skipped: {summary} on {start_date}")
                    return f"Event already exists for {start_date}: {summary}"

            event = {
                "summary": f"📋 {summary}",
                "description": f"Contract Deliverable\n\n{description}",
                "start": {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": "America/Los_Angeles"
                },
                "end": {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": "America/Los_Angeles"
                },
                "attendees": [{"email": user_email}],
                "reminders": {
                    "useDefault": True,
                },
            }

            created_event = service.events().insert(
                calendarId="primary",
                body=event,
                sendUpdates="all"  # This sends invitations to attendees
            ).execute()

            event_link = created_event.get('htmlLink', 'No link available')
            return f"✅ Calendar event created and invitation sent!\nEvent: {summary}\nDate: {start_date}\nInvited: {user_email}\nLink: {event_link}"
            
        except HttpError as error:
            return f"❌ Google Calendar API error: {str(error)}"
        except Exception as e:
            return f"❌ Failed to create calendar event: {str(e)}"