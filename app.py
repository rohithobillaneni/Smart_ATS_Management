from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import json
import sqlite3
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from io import BytesIO
import PyPDF2
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ZAPIER_WEBHOOK_URL = os.getenv("ZAPIER_WEBHOOK_URL")

if not GOOGLE_API_KEY:
    raise Exception("GOOGLE_API_KEY is not set")

genai.configure(api_key=GOOGLE_API_KEY)

# Setup Flask
app = Flask(__name__)
CORS(app)

# DB Path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "ats_results.db")

# Create tables if they don't exist
def create_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Job Descriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Results table with PDF stored as blob
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            job_description_id INTEGER NOT NULL,
            resume_name TEXT,
            resume_file BLOB,
            match_percent TEXT,
            summary TEXT,
            matched_keywords TEXT,
            missing_keywords TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(job_description_id) REFERENCES job_descriptions(id)
        )
    ''')

    conn.commit()
    conn.close()

create_tables()

# Gemini Evaluation Logic
def evaluate_resume_with_gemini(resume_text, jd_text):
    prompt = f"""
You are an intelligent ATS system evaluating candidates for tech roles.
Compare the resume with the job description and return structured JSON with:
- "JD Match": "XX%"
- "MatchedKeywords": [{{"keyword": "Python", "reason": "..."}}, ...]
- "MissingKeywords": [{{"keyword": "Docker", "reason": "..."}}, ...]
- "Profile Summary": "..."
Resume:
{resume_text}

Job Description:
{jd_text}
"""
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    clean_output = response.text.strip().replace("**", "").replace("```json", "").replace("```", "")
    return json.loads(clean_output)

# Home Route
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# Fetch all JDs (API)
@app.route("/api/job_descriptions", methods=["GET"])
def get_job_descriptions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description FROM job_descriptions ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    jds = [{"id": row[0], "title": row[1], "description": row[2]} for row in rows]
    return jsonify(jds)

@app.route("/job/<int:jd_id>", methods=["GET"])
def job_page(jd_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description FROM job_descriptions WHERE id = ?", (jd_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return "<h2>Job not found</h2>", 404

    return render_template("job.html", id=row[0], title=row[1], description=row[2])


# Submit Form Endpoint
@app.route("/submit-form", methods=["POST"])
def submit_form():
    try:
        name = request.form["name"]
        email = request.form["email"]
        job_description_id = int(request.form["job_description_id"])
        file = request.files["resume"]

        if not file or not file.filename.endswith(".pdf"):
            return jsonify({"error": "Invalid file type (PDF required)"}), 400

        resume_binary = file.read()
        filename = secure_filename(file.filename)

        # Fetch job description text
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM job_descriptions WHERE id=?", (job_description_id,))
        jd_row = cursor.fetchone()

        if not jd_row:
            return jsonify({"error": "Invalid job description ID"}), 400

        jd_text = jd_row[0]

        # Extract resume text
        reader = PyPDF2.PdfReader(BytesIO(resume_binary))
        resume_text = " ".join(page.extract_text() or "" for page in reader.pages)

        # Get evaluation
        ats_result = evaluate_resume_with_gemini(resume_text, jd_text)

        # Save result to DB
        cursor.execute('''
            INSERT INTO results
            (name, email, job_description_id, resume_name, resume_file, match_percent, summary, matched_keywords, missing_keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, email, job_description_id, filename, resume_binary,
            ats_result.get("JD Match", "0%"),
            ats_result.get("Profile Summary", "N/A"),
            json.dumps(ats_result.get("MatchedKeywords", [])),
            json.dumps(ats_result.get("MissingKeywords", []))
        ))

        conn.commit()
        conn.close()

        # Notify Zapier (optional)
        if ZAPIER_WEBHOOK_URL:
            zapier_payload = {
                "name": name,
                "email": email,
                "job_description_id": job_description_id
            }
            try:
                zapier_response = requests.post(ZAPIER_WEBHOOK_URL, json=zapier_payload)
                if zapier_response.status_code != 200:
                    app.logger.warning(f"Zapier webhook failed: {zapier_response.status_code} - {zapier_response.text}")
            except Exception as zapier_error:
                app.logger.warning(f"Zapier webhook exception: {zapier_error}")

        return render_template("thankyou.html")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Start the Flask server
if __name__ == "__main__":
    app.run(debug=True)
