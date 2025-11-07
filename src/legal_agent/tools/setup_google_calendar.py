#!/usr/bin/env python3
"""
Simple OAuth setup for Google Calendar
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Required scope for creating events and inviting users
SCOPES = ['https://www.googleapis.com/auth/calendar']

def setup_oauth():
    print("🔐 Simple Google Calendar OAuth Setup")
    print("=" * 45)
    
    # Save your downloaded credentials as 'desktop_credentials.json'
    credentials_file = '../../../desktop_credentials.json'
    
    try:
        # Create the flow using the client secrets file
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_file, 
            SCOPES
        )
        
        print("🌐 Opening browser for authentication...")
        print("Please sign in with your Google account and grant calendar permissions.")
        print()
        
        # Run the flow - this will open a browser
        creds = flow.run_local_server(port=0)
        
        # Save the credentials for later use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        
        print("💾 Credentials saved to token.json")
        
        # Test the connection
        service = build('calendar', 'v3', credentials=creds)
        calendar = service.calendars().get(calendarId='primary').execute()
        
        print(f"✅ Success! Connected to: {calendar['summary']}")
        print("🎉 OAuth setup complete! You can now invite users to calendar events.")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ {credentials_file} not found!")
        print("\n📋 To fix:")
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Create OAuth 2.0 Client ID")
        print("3. Application type: Desktop Application") 
        print("4. Download the JSON file")
        print("5. Save it as 'desktop_credentials.json' in this folder")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    setup_oauth()