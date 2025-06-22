# 📄 Smart ATS Management

An AI-powered resume evaluation and applicant tracking system that combines a **Streamlit admin interface** and a **Flask backend API** to efficiently manage job descriptions, evaluate candidate resumes against roles using Google Gemini AI, and automate workflows with Zapier.

---

## 🚀 Features

- 📝 **Job Description Management**  
  Add, edit, and delete job descriptions to keep roles up to date.

- 📄 **Candidate Resume Submission**  
  Candidates upload their resumes (PDF) along with name and email via the Flask backend.

- 🤖 **AI-Powered Resume Evaluation**  
  Using Google Gemini 2.0 Flash, the app analyses resumes against job descriptions, returning:  
  - Match percentage score  
  - Matched keywords with reasons  
  - Missing keywords with reasons  
  - AI-generated profile summary  

- ✅ **Detailed Keyword Insights**  
  Clear display of matched and missing keywords side-by-side, aiding recruiters to quickly understand candidate fit.

- 📈 **Candidate Ranking and History**  
  Track all evaluations, sort/filter by match score or date, and rank candidates for each job description.

- 📥 **Downloadable Reports**  
  Download summary reports and candidate resumes directly from the UI.

- 🔗 **Zapier Integration for Automation**  
  When a resume is evaluated, a summary is optionally sent automatically to a Zapier webhook. This enables:  
  - Automated email notifications  
  - Integration with applicant tracking systems (ATS) or CRMs  
  - Further workflow automation (e.g., Slack alerts, Google Sheets updates)

- 🌐 **Flask Backend API**  
  Provides endpoints for resume submissions and serves web pages (`index.html`, `job.html`, `thankyou.html`), offering a user-friendly candidate-facing submission portal.

---

## 🖥️ App Overview

### Streamlit Admin Panel (`admin.py`)

- Manage job descriptions and view/add/edit/delete roles  
- Upload candidate resumes, evaluate with AI, and save results  
- View evaluation history with filters and search  
- Rank candidates by match score for each job  

### Flask Backend (`app.py`)

- Candidate-facing web app with submission form  
- Receives name, email, JD text, and resume (PDF)  
- Evaluates resume using Gemini AI, saves results to SQLite  
- Sends evaluation summary to Zapier webhook (optional)  
- Serves simple HTML pages to thank candidates after submission  

---

## 📦 Installation & Usage

### Requirements

- Python 3.8+  
- Google API Key (Gemini AI)  
- Optional: Zapier account and webhook URL for automation  

### Setup Instructions

1. **Clone the repository**

```bash
git clone https://github.com/rohithobillaneni/Smart_ATS_Management.git
cd Smart_ATS_Management
````

2. **Create and activate a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file at the project root with:

```env
GOOGLE_API_KEY=your_google_api_key_here
ZAPIER_WEBHOOK_URL=your_zapier_webhook_url_here  # Optional, leave empty if not using Zapier
```

5. **Run Streamlit admin interface**

```bash
streamlit run admin.py
```

6. **Run Flask backend for candidate submissions (optional)**

```bash
python app.py
```

Visit `http://localhost:5000` to access the candidate submission portal.

---

## 📁 Project Structure

```
Smart_ATS_Management/
│
├── admin.py                 # Streamlit admin app (manage JDs, evaluate resumes)
├── app.py                   # Flask backend API & candidate submission web app
├── templates/               # Flask HTML templates (index.html, job.html, thankyou.html)
├── ats_results.db           # SQLite database storing JDs and evaluation results
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (API keys, webhook URLs)
├── README.md                # Project documentation (this file)
└── other supporting files
```

---

## 🤖 How Zapier Integration Works

* When a candidate submits their resume, the backend evaluates it using Gemini AI.
* The evaluation summary is sent as JSON payload to the Zapier webhook URL specified in `.env`.
* Zapier can then trigger workflows such as:

  * Sending a customised email notification to recruiters
  * Logging candidate info and evaluation results in Google Sheets or Airtable
  * Notifying a Slack channel or other communication tool
* This automation reduces manual work and speeds up candidate processing.

---

## 🤝 Contributions

Feel free to fork the repo, raise issues, or submit pull requests to improve this project!

---

## 🛡️ Disclaimer

This tool is a supportive aid designed to streamline resume evaluation using AI and automation. It should not replace comprehensive human review and decision-making.

---

## 📧 Contact

Created by **Rohith Obillaneni**
📩 [rohithobillaneni92@gmail.com](mailto:rohithobillaneni92@gmail.com)
📍 Luton, UK
🔗 [LinkedIn](https://www.linkedin.com/in/rohithobillaneni)

---

## 📜 Licence

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

