from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from src.legal_agent.brand_legal_crew import ContentCreatorLegalCrew
from src.legal_agent.legal_crew import LegalAgent
import os
import pdfplumber
from datetime import date, datetime, timedelta
import threading
import time
from dotenv import load_dotenv
from werkzeug.security import check_password_hash
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import markdown2
import re
import json
import pytz
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv()

os.environ["CREWAI_TRACING_ENABLED"] = "0"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "1"
os.environ["CREWAI_DISABLE_TRACING"] = "1"
os.environ["CREWAI_TELEMETRY"] = "0"
os.environ["OTEL_SDK_DISABLED"] = "1"

app = Flask(__name__)
# Use a fixed secret key for session consistency, but ensure it changes in production
app.secret_key = os.getenv("SECRET_KEY") or "dev-secret-key-change-in-production"

# Load hashed password
APP_PASSWORD_HASH = os.getenv("APP_PASSWORD_HASH")
if not APP_PASSWORD_HASH:
    raise RuntimeError("APP_PASSWORD_HASH is not set in the environment.")

# -------------------------
# Session Configuration
# -------------------------
@app.before_request
def before_request():
    """Initialize session with default values if they don't exist"""
    if 'mode' not in session:
        session['mode'] = 'legal'  # Default mode
    # Ensure session is saved
    session.modified = True

# -------------------------
# Email Functions
# -------------------------
def send_summary_email(recipient: str, subject: str, summary_file: str):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("EMAIL_PASSWORD")
    
    if not sender_email or not sender_password:
        raise RuntimeError("Missing email credentials")
    
    with open(summary_file, "r", encoding="utf-8") as f:
        summary_text = f.read()

    summary_text = summary_text.strip()
    if summary_text.startswith("```"):
        summary_text = summary_text[summary_text.find("\n")+1:]
    if summary_text.endswith("```"):
        summary_text = summary_text[:summary_text.rfind("\n")]

    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = recipient
    msg["Subject"] = subject

    full_body = f"{summary_text}\n\n"
    html_body = markdown2.markdown(full_body)
    plain_part = MIMEText(full_body, "plain")
    html_part = MIMEText(html_body, "html")
    
    msg.attach(plain_part)
    msg.attach(html_part)
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)

    return f"✅ Email successfully sent to {recipient}"

def extract_company_name(contract_text: str) -> str:
    patterns = [
        r"between\s+(.*?)\s+(?:and|&)",
        r"by and between\s+(.*?)\s+(?:and|&)",
        r"entered into by\s+(.*?)\s+(?:and|&)",
        r"Agreement is made between\s+(.*?)\s+(?:and|&)",
        r"This Agreement is made by\s+(.*?)\s+(?:and|&)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, contract_text, flags=re.IGNORECASE)
        if match:
            possible_name = match.group(1).strip()
            if len(possible_name.split()) <= 6 and not possible_name.lower().startswith("the influencer"):
                return possible_name.replace('"', '').replace("'", "")
    
    company_match = re.search(r"\b([A-Z][A-Za-z0-9&,\.\s]+(?:Inc\.|LLC|Ltd\.|Corporation|Company))\b", contract_text)
    if company_match:
        return company_match.group(1).strip()

    return ""

# -------------------------
# Calendar Functions
# -------------------------
def send_calendar_invites(user_email: str) -> str:
    """Send calendar invites for deliverables found in calendar_deliverables.json"""
    try:
        # Check if deliverables file exists
        if not os.path.exists('calendar_deliverables.json'):
            return "No calendar deliverables found."
        
        with open('calendar_deliverables.json', 'r') as f:
            deliverables = json.load(f)
        
        if not deliverables:
            return "No deliverables to process."
        
        # Get Google Calendar credentials
        token_json_str = os.getenv('GOOGLE_CALENDAR_TOKEN_JSON')
        if not token_json_str:
            return "Calendar not configured."
        
        token_data = json.loads(token_json_str)
        creds = Credentials.from_authorized_user_info(token_data, ['https://www.googleapis.com/auth/calendar'])
        
        # Refresh token if needed
        if not creds.valid and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        
        service = build('calendar', 'v3', credentials=creds)
        
        results = []
        created_count = 0
        existing_count = 0
        
        for deliverable in deliverables:
            result = create_calendar_event(service, deliverable, user_email)
            if "created" in result.lower():
                created_count += 1
            elif "exists" in result.lower():
                existing_count += 1
            results.append(result)
        
        summary = f"Calendar invites: {created_count} created, {existing_count} existing"
        return summary
        
    except Exception as e:
        return f"Calendar error: {str(e)}"

def create_calendar_event(service, deliverable: dict, user_email: str) -> str:
    """Create a single calendar event with duplicate checking."""
    try:
        summary = deliverable.get('summary', '')
        description = deliverable.get('description', '')
        start_date = deliverable.get('start_date', '')
        
        if not all([summary, start_date]):
            return f"Skipped: Missing data for {summary}"
        
        # Parse date and set to 9 AM PST
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        pst = pytz.timezone('America/Los_Angeles')
        start_dt = pst.localize(start_dt.replace(hour=9, minute=0, second=0, microsecond=0))
        end_dt = start_dt + timedelta(hours=1)
        
        # Check for existing events
        time_min = (start_dt - timedelta(days=1)).isoformat()
        time_max = (start_dt + timedelta(days=2)).isoformat()
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            q=summary[:20],  # Search by title
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        for event in events:
            existing_summary = event.get('summary', '').lower()
            if f"📋 {summary}".lower() in existing_summary:
                return f"Exists: {summary} on {start_date}"
        
        # Create new event
        event = {
            "summary": f"📋 {summary}",
            "description": f"Contract Deliverable\n\n{description}",
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "America/Los_Angeles"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "America/Los_Angeles"},
            "attendees": [{"email": user_email}],
            "reminders": {"useDefault": True},
        }
        
        created_event = service.events().insert(
            calendarId="primary",
            body=event,
            sendUpdates="all"
        ).execute()
        
        return f"Created: {summary} on {start_date}"
        
    except Exception as e:
        return f"Error with {summary}: {str(e)}"

# -------------------------
# Authentication helpers
# -------------------------
def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if check_password_hash(APP_PASSWORD_HASH, password):
            session.clear()  # Clear any old session data
            session["logged_in"] = True
            session["mode"] = "legal"  # Set default mode on login
            next_url = request.args.get("next") or url_for("index")
            return redirect(next_url)
        else:
            return render_template("login.html", error="Invalid password"), 403
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------------------------
# Protected routes
# -------------------------
@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/set_mode/<mode>", methods=["POST"])
@login_required
def set_mode(mode):
    if mode not in ["legal", "creator"]:
        return jsonify({"success": False, "message": "Invalid mode"}), 400
    session["mode"] = mode
    session.modified = True  # Ensure session is saved
    print(f"🔄 Switched mode to: {mode}")
    return jsonify({"success": True, "mode": mode})

@app.route("/get_mode", methods=["GET"])
@login_required
def get_mode():
    """Get the current mode - useful for page reloads"""
    return jsonify({"mode": session.get("mode", "legal")})

# --- Configuration ---
CREW_TIMEOUT = 15 * 60

def run_crew_with_timeout(crew, inputs, timeout=CREW_TIMEOUT):
    result_container = [None]
    def target():
        try:
            import os
            os.environ["CREWAI_INTERACTIVE"] = "0"
            result_container[0] = crew.kickoff(inputs=inputs)
        except Exception as e:
            result_container[0] = e

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise TimeoutError("⏰ Crew run exceeded 15 minutes. Aborting.")
    return result_container[0]

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    mode = session.get("mode", "legal")
    contract_file = request.files.get("contract")
    user_email = request.form.get("user_email")

    if not contract_file or not user_email:
        return jsonify({"success": False, "message": "Missing file or email"}), 400

    try:
        with pdfplumber.open(contract_file.stream) as pdf:
            contract_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        
        company_name = extract_company_name(contract_text)
        print(f"🧾 Detected company name: {company_name}")

        today = date.today()
        subject_line = f"Contract Summary Report - {today} - {company_name}" if company_name else f"Contract Summary Report - {today}"

        if mode == "creator":
            print("🎬 Using Content Creator Legal Agent crew")
            crew = ContentCreatorLegalCrew().crew()
        else:
            print("⚖️ Using Base Legal Agent crew")
            crew = LegalAgent().crew()

        result = run_crew_with_timeout(
            crew,
            inputs={"user_email": user_email, "contract_text": contract_text},
            timeout=CREW_TIMEOUT
        )

        print("✅ Crew completed with result:", result)

        try:
            # Send email summary
            summary_file = "contract_summary.md"
            send_summary_email(user_email, subject_line, summary_file)
            
            # Send calendar invites (only for creator mode)
            calendar_result = ""
            if mode == "creator":
                calendar_result = send_calendar_invites(user_email)
                print(f"📅 Calendar result: {calendar_result}")
            
            message = f"Contract processed! Check your email ({user_email})."
            if calendar_result:
                message += f" {calendar_result}"
                
            return jsonify({"success": True, "message": message})
            
        except Exception as e:
            return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"success": False, "message": f"Crew Error: {str(e)}"}), 500

# if __name__ == "__main__":
#     app.run(debug=True)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)