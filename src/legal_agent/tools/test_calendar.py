#!/usr/bin/env python3
"""
Quick test for Google Calendar tool
"""

import os
from google_calendar_tool import SimpleGoogleCalendarTool
from datetime import datetime, timedelta

# Test with tomorrow's date
tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

tool = SimpleGoogleCalendarTool()
result = tool._run(
    summary="Quick Test Event",
    description="Test from LegalAgent - please delete",
    start_date=tomorrow,
    user_email="yodude36tc@gmail.com"  # Change to your email
)

print("🔧 TEST RESULT:")
print(result)