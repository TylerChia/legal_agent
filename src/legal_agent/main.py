#!/usr/bin/env python
import sys
import warnings
import json
from datetime import datetime
from legal_agent.legal_crew import LegalAgent
from datetime import date, datetime

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# =============================
# MAIN EXECUTION ENTRY POINT
# =============================

def run():
    """
    Run the LegalAgent crew end-to-end:
    1. Parse a contract
    2. Analyze risks
    3. Research unclear clauses
    4. Summarize for the user
    5. Email the summary
    """
    # Replace this with your test input or integrate with file upload in your app
    contract_text = """
    This contract is between Company A and Client B. The client agrees to pay $10,000 within 30 days.
    Confidentiality must be maintained for all information shared.
    Either party may terminate the agreement with 60 days’ notice.
    """

    user_email = "tylerchia7@gmail.com"
    today = date.today()
    subject_line = "Contract Summary Report" + " " + str(today)

    try:
        result = LegalAgent().crew().kickoff(inputs={"user_email": user_email, "contract_text": contract_text})

        print("\n✅ Contract review completed successfully.")
        print("📄 Summary and risk report generated.\n")
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")



def run_with_trigger():
    """
    Run the crew from a trigger payload (e.g. API call, webhook, or app frontend).
    Usage: python main.py run_with_trigger '{"contract_text": "...", "user_email": "..."}'
    """
    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "contract_text": trigger_payload.get("contract_text", ""),
        "user_email": trigger_payload.get("user_email", ""),
        "current_year": str(datetime.now().year)
    }

    try:
        result = LegalAgent().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")


# ====================================================
# Command Line Entrypoint
# ====================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python main.py run")
        print("  python main.py train <iterations> <filename>")
        print("  python main.py replay <task_id>")
        print("  python main.py test <iterations> <eval_llm>")
        print("  python main.py run_with_trigger '<json_payload>'")
        sys.exit(1)

    command = sys.argv[1]
    if command == "run":
        run()
    elif command == "run_with_trigger":
        run_with_trigger()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
