from flask import Flask, render_template, request, jsonify
from src.legal_agent.crew import LegalAgent
import os
import pdfplumber
from datetime import date

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    contract_file = request.files.get("contract")
    user_email = request.form.get("user_email")

    if not contract_file or not user_email:
        return jsonify({"success": False, "message": "Missing file or email"}), 400

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], contract_file.filename)
    contract_file.save(file_path)

    # Extract PDF text
    with pdfplumber.open(file_path) as pdf:
        contract_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    today = date.today()
    subject_line = f"Contract Summary Report {today}"

    try:
        LegalAgent().crew().kickoff(
            inputs={
                "user_email": user_email,
                "subject_line": subject_line,
                "contract_text": contract_text,
            }
        )
        return jsonify({"success": True, "message": f"Contract processed! Check your email ({user_email})."})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
