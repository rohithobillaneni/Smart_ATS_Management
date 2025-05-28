import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import re
import json

# Set page config early
st.set_page_config(page_title="Smart ATS Evaluator", layout="wide", initial_sidebar_state="expanded")

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    st.sidebar.error("Google API key not found. Please check your .env.")
    st.stop()

# Apply custom styles for consistent branding and layout
st.markdown("""
    <style>
    .main-header {
        font-size: 2.8rem;
        color: #1f4e79;
        margin-bottom: 0.5em;
    }
    .highlight {
        background-color: #ffebcc;
        padding: 0.3rem 0.4rem;
        border-radius: 1px;
        margin: 0.5px;
        display: inline-block;
        font-weight: 400;
    }
    </style>
""", unsafe_allow_html=True)

# Extract text from uploaded PDF resume
def input_pdf_text(uploaded_file):
    try:
        reader = pdf.PdfReader(uploaded_file)
        return "".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

# Interact with Gemini API and generate ATS evaluation in JSON format
def get_ats_evaluation(resume_text, job_desc):
    prompt = f"""
You are an intelligent ATS system evaluating candidates for tech roles.
Compare the resume with the job description and return structured JSON with:

- "JD Match": "XX%"
- "MatchedKeywords": [{{"keyword": "Python", "reason": "Mentioned in experience section as a key skill"}}, ...]
- "MissingKeywords": [{{"keyword": "Docker", "reason": "Not mentioned anywhere in the resume"}}, ...]
- "Profile Summary": "Brief summary of strengths, tech stack, alignment with job."

Resume:
{resume_text}

Job Description:
{job_desc}
"""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error from Gemini API: {e}"


# Sidebar inputs for JD and Resume
st.sidebar.header("🔍 ATS Evaluation")
jd = st.sidebar.text_area("Paste Job Description", height=200)
uploaded_file = st.sidebar.file_uploader("Upload Resume (PDF)", type="pdf")
run = st.sidebar.button("Evaluate")

# Main title of the app
st.markdown("<h1 class='main-header'>📄 Smart ATS Evaluator</h1>", unsafe_allow_html=True)
st.write("Use AI to analyse and optimise your resume for a job description.")

# Run evaluation only when inputs are valid and user clicks "Evaluate"
if run:
    if not uploaded_file or not jd.strip():
        st.warning("Please provide both a job description and resume.")
    else:
        with st.spinner("Analysing resume..."):
            resume_text = input_pdf_text(uploaded_file)
            raw_output = get_ats_evaluation(resume_text, jd)

            # Clean Gemini's output for valid JSON parsing
            raw_output_clean = raw_output.replace("**", "").replace("```json", "").replace("```", "")

            # Attempt to parse cleaned output as JSON
            try:
                raw_json = json.loads(raw_output_clean)
            except json.JSONDecodeError:
                st.error("⚠️ Failed to parse output. Showing raw response instead.")
                raw_json = {"response": raw_output_clean}

        # ----- Tabs for UI presentation -----
        tab1, tab2 = st.tabs(["📊 Result", "📄 Detailed View"])

        # ----- Tab 1: Result Summary -----
        with tab1:
            st.subheader("📈 Match Score")

            # Extract and display JD Match score
            score_str = raw_json.get("JD Match", "0%")
            score = int(score_str.replace("%", "")) if "%" in score_str else 0
            st.metric("JD Match", f"{score}%")
            st.progress(score)

            # Create two columns for side-by-side view
            col1, col2 = st.columns(2)

            # ---- Matched Keywords (left) ----
            with col1:
                st.subheader("✅ Matched Keywords")
                matched = raw_json.get("MatchedKeywords", [])
                if isinstance(matched, list) and matched:
                    for item in matched:
                        keyword = item.get("keyword", "")
                        reason = item.get("reason", "")
                        st.markdown(
                            f"<span class='highlight'>{keyword}</span>",
                            unsafe_allow_html=True
                        )
                else:
                    st.write("No specific keywords matched.")

            # ---- Missing Keywords (right) ----
            with col2:
                st.subheader("❌ Missing Keywords")
                missing = raw_json.get("MissingKeywords", [])
                if isinstance(missing, list) and missing:
                    for item in missing:
                        keyword = item.get("keyword", "")
                        reason = item.get("reason", "")
                        st.markdown(
                            f"<span class='highlight'>{keyword}</span>",
                            unsafe_allow_html=True
                        )
                else:
                    st.write("No major keywords missing. ✅")

            # ---- Profile Summary and Download ----
            st.subheader("🧾 Profile Summary")
            summary = raw_json.get("Profile Summary", "No summary generated.")
            st.write(summary)

            # Allow download of the profile summary as text
            st.download_button(
                label="⬇️ Download Summary",
                data=summary,
                file_name="profile_summary.txt"
            )

        # ----- Tab 2: Raw JSON output (detailed) -----
        with tab2:
            st.subheader("📄 More Detailed Output")
            score_str = raw_json.get("JD Match", "0%")
            score = int(score_str.replace("%", "")) if "%" in score_str else 0
            st.metric("JD Match", f"{score}%")
            st.progress(score)

            st.subheader("❌ Missing Keywords")
            if isinstance(raw_json.get("MissingKeywords"), list):
                for item in raw_json["MissingKeywords"]:
                    st.markdown(
                        f"<span class='highlight'>{item['keyword']}</span>: {item['reason']}",
                        unsafe_allow_html=True
                    )
            else:
                st.write("No major keywords missing. ✅")

            st.subheader("✅ Matched Keywords")
            if isinstance(raw_json.get("MatchedKeywords"), list):
                for item in raw_json["MatchedKeywords"]:
                    st.markdown(
                        f"<span class='highlight'>{item['keyword']}</span>: {item['reason']}",
                        unsafe_allow_html=True
                    )
            else:
                st.write("No specific keywords matched.")



