# 📄 Smart ATS Management

An AI-powered resume evaluation and applicant tracking system that combines a **Streamlit-based admin interface** with a **Flask backend API**. It enables recruiters to efficiently manage job descriptions, evaluate candidate resumes using **Google Gemini AI**, and automate workflows with **Zapier** integration.

---

## 🚀 Features

### 🧠 Streamlit Admin Interface

* 📝 **Job Description Management**
  Easily add, edit, and delete job descriptions.

  Add JD
  ![Add JD](https://github.com/user-attachments/assets/a52ad6fe-cb30-4a5e-9335-fb270accf75c)

  Edit/Delete
  ![Edit/Delete JD](https://github.com/user-attachments/assets/5aa35ba8-7dae-4509-8ba2-1296aa76b35d)

* 🤖 **AI-Powered Resume Evaluation**
  Uses Gemini 2.0 Flash to evaluate resumes against selected job descriptions and generates:

  * ✅ Match percentage score
  * ✅ Matched keywords with context
  * ❌ Missing keywords with reasons
  * 🧾 AI-generated profile summary

  ![Evaluation Result](https://github.com/user-attachments/assets/de67579b-9a5e-4057-9767-21d8b48d11dd)

* 📈 **Candidate Ranking and History**
  Automatically store and rank candidates by JD match. View, sort, and filter past evaluations.

  ![History](https://github.com/user-attachments/assets/13f2e127-f39f-4b4f-91e9-65c026277821)

  Ranking the Candidates applied for JD
  
  ![Rank Candidates](https://github.com/user-attachments/assets/3aa00f89-854f-4406-a215-c852ed4b26b7)

* 📥 **Downloadable Reports**
  Export candidate summaries and keyword insights for offline use or sharing.

---

### 🌐 Flask Candidate Portal

* 📄 **Resume Submission Form**
  Simple front-end (`index.html`, `job.html`) lets candidates upload their name, email, JD, and PDF resume.
  Open Positions
  
  <img width="1470" alt="Screenshot 2025-06-22 at 18 28 26" src="https://github.com/user-attachments/assets/64cbbf12-0ca6-4818-87c7-c1c1eb1e939b" />

  Application Form
  ![Candidate Submission](https://github.com/user-attachments/assets/ecf70581-4e75-457b-9b05-26c8928932d8)

* 📨 **Thank You Page + Zapier Automation**
  After submission, candidates are redirected to a thank-you page. Summary is optionally sent via Zapier to automate email replies, ATS entries, or Slack updates.

  ![Thank You Page](https://github.com/user-attachments/assets/0fcdbd5f-aed1-41fb-8ff8-fa705639cd74)

---

## 🖥️ App Overview

### Streamlit Admin Panel (`admin.py`)

* Manage job roles
* Evaluate uploaded resumes using Gemini
* View history and rank candidates

### Flask Backend (`app.py`)

* Candidate-facing submission form
* AI evaluation triggered via API
* Summary optionally sent to Zapier webhook
* Serves HTML templates (`index.html`, `job.html`, `thankyou.html`)

---

## 📦 Installation & Usage

### Requirements

* Python 3.8+
* Google API key (Gemini)
* Zapier Webhook URL (optional)

### Setup Instructions

1. **Clone the Repository**

```bash
git clone https://github.com/rohithobillaneni/Smart_ATS_Management.git
cd Smart_ATS_Management
```

2. **Create and Activate Virtual Environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Set Up Environment Variables**
   Create a `.env` file:

```env
GOOGLE_API_KEY=your_google_api_key
ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/xxxxxxx  # Optional
```

5. **Run the Admin Panel**

```bash
streamlit run admin.py
```

6. **Run the Flask Backend (Optional for Candidate Submissions)**

```bash
python app.py
```

Visit `http://localhost:5000` to see the candidate form.

---

## 📁 Project Structure

```
Smart_ATS_Management/
├── admin.py                 # Streamlit admin interface
├── app.py                   # Flask backend for submissions
├── templates/
│   ├── index.html           # Candidate landing page
│   ├── job.html             # Resume upload form
│   └── thankyou.html        # Confirmation page
├── ats_results.db           # SQLite database
├── requirements.txt         # Dependencies
├── .env                     # API keys & webhook URLs
└── README.md                # Project documentation
```

---

## 🔗 How Zapier Integration Works

1. Candidate uploads resume via Flask frontend.
2. Gemini AI evaluates and generates a summary.
3. If a `ZAPIER_WEBHOOK_URL` is provided, the summary is sent as JSON to the webhook.
4. Zapier handles:

   * Email confirmation to candidate
   * Logging to Google Sheets or Airtable
   * Slack notification to recruiter
   * Integration with ATS or CRM

---

## 🤝 Contributions

Open to suggestions, issues, and pull requests!
If you find this project useful, consider starring ⭐ the repo or sharing it.

---

## 📧 Contact

**Rohith Obillaneni**
📍 Luton, UK
📩 [rohithobillaneni92@gmail.com](mailto:rohithobillaneni92@gmail.com)
🔗 [LinkedIn](https://www.linkedin.com/in/rohithobillaneni)

---

## 📜 Licence

This project is licensed under the MIT Licence.
See the [LICENSE](LICENSE) file for full details.

---
