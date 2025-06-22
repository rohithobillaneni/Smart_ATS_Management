import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
from sqlalchemy import (
    create_engine, Column, String, Integer, Text, DateTime, LargeBinary, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import datetime
from sqlalchemy.orm import joinedload
import base64
import pytz
import pandas as pd

# Set page config early
st.set_page_config(page_title="Smart ATS Management", layout="wide", initial_sidebar_state="expanded")

# Load environment variables
load_dotenv()

Base = declarative_base()

class JobDescription(Base):
    __tablename__ = 'job_descriptions'
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    evaluations = relationship(
        "EvaluationResult",
        back_populates="job_description_rel",
        cascade="all, delete-orphan"
    )


class EvaluationResult(Base):
    __tablename__ = 'results'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    resume_name = Column(String)
    resume_file = Column(LargeBinary)
    job_description_id = Column(Integer, ForeignKey('job_descriptions.id'))
    match_percent = Column(String)
    summary = Column(Text)
    matched_keywords = Column(Text)
    missing_keywords = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    job_description_rel = relationship("JobDescription", back_populates="evaluations")

# --- Create DB ---
engine = create_engine('sqlite:///ats_results.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    st.sidebar.error("Google API key not found. Please check your .env.")
    st.stop()

# Custom CSS (as you had it)
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
    .stTabs [data-baseweb="tab"] {
        font-size: 24px;
        font-weight: bold;
    }
    .stButton>button {
        background-color: #28a745;
        color: white;
        font-size: 18px;
        padding: 10px 24px;
    }
    details:hover {
        box-shadow: 0px 0px 6px rgba(0,0,0,0.2);
        border-radius: 6px;
    }
    .element-container:has(.stRadio) label {
        font-size: 20px;
        padding: 8px;
        font-weight: 600;
    }
    .stRadio [role="radiogroup"] > div {
        padding: 16px 16px;
        border-radius: 20px;
        margin-bottom: 6px;
        font-weight: bold;
        border: 12px solid #aaa;
    }
    .stRadio [role="radiogroup"] > div:hover {
        background-color: #e6f2ff;
    }
    div[role="button"] > div:first-child {
            font-size: 26px !important;
            font-weight: 700 !important;
            color: #004a99 !important;
            padding: 10px 16px !important;
            background-color: #d0e4ff !important;
            border-radius: 8px;
            margin-bottom: 8px;
            cursor: pointer;
            letter-spacing: 0.4px;
        }
        .stExpander > div > div > div > div {
            font-size: 18px !important;
            line-height: 1.5 !important;
            padding: 16px 24px !important;
            background-color: #f5faff !important;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            margin-bottom: 24px;
            color: #1a2d50;
        }
        .candidate-field {
            margin-bottom: 10px;
            font-size: 18px;
        }
        .candidate-label {
            font-weight: 700;
            color: #103060;
        }
        a {
            color: #0066cc;
            text-decoration: none;
            font-weight: 700;
        }
        a:hover {
            text-decoration: underline;
        }
        .evaluation-field {
            margin-bottom: 10px;
            font-size: 18px;
        }
        .evaluation-label {
            font-weight: 700;
            color: #1a2d59;
        }
            
    </style>
""", unsafe_allow_html=True)


# Helper: generate clickable download link for resume PDF
def get_resume_download_link(evaluation):
    resume_b64 = base64.b64encode(evaluation.resume_file).decode('utf-8')
    href = f'<a href="data:application/pdf;base64,{resume_b64}" download="{evaluation.resume_name}">Download Resume 📂</a>'
    return href

# PDF Text Extraction
def input_pdf_text(uploaded_file):
    try:
        reader = pdf.PdfReader(uploaded_file)
        return "".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

# Gemini API Call
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

# Sidebar Navigation
view_option = st.sidebar.radio("Select the Service", ["🧠 Evaluate", "📋 Manage JDs", "📜 History", "📈 Candidate Ranking"])

if view_option == "📋 Manage JDs":
    st.markdown("<h2 class='main-header'>📋 Manage Job Descriptions</h2>", unsafe_allow_html=True)
    session = Session()

    # Fetch all job descriptions ordered by creation date desc
    jds = session.query(JobDescription).order_by(JobDescription.created_at.desc()).all()

    # --- Add New JD Form ---
    with st.form("add_jd_form"):
        st.subheader("➕ Add New Job Description")
        new_title = st.text_input("Job Title", key="new_jd_title")
        new_desc = st.text_area("Job Description", height=180, key="new_jd_desc")
        add_jd = st.form_submit_button("Add Job Description")

        if add_jd:
            if not new_title.strip() or not new_desc.strip():
                st.warning("Please provide both a title and description.")
            else:
                existing = session.query(JobDescription).filter_by(title=new_title.strip()).first()
                if existing:
                    st.error("Job Title already exists. Please choose a different title.")
                else:
                    jd = JobDescription(title=new_title.strip(), description=new_desc.strip())
                    session.add(jd)
                    session.commit()
                    st.success(f"Added new Job Description: '{new_title.strip()}'")
                    st.rerun()

    st.markdown("---")

    if not jds:
        st.info("No job descriptions found. Use the form above to add one.")
        session.close()
        st.stop()

    st.subheader("📑 Existing Job Descriptions")

    # Loop through each JD and show expanders with update/delete options
    for jd in jds:
        with st.expander(f"{jd.title} (Added {jd.created_at.strftime('%Y-%m-%d')})", expanded=False):
            st.write(jd.description)

            # Button to enable edit mode for this JD
            if st.button(f"Edit '{jd.title}'", key=f"edit_{jd.id}"):
                st.session_state[f"edit_mode_{jd.id}"] = True

            # Show update form if in edit mode
            if st.session_state.get(f"edit_mode_{jd.id}", False):
                with st.form(f"update_jd_form_{jd.id}"):
                    updated_title = st.text_input("Update Title", value=jd.title, key=f"update_title_{jd.id}")
                    updated_desc = st.text_area("Update Description", value=jd.description, height=180, key=f"update_desc_{jd.id}")
                    update_btn = st.form_submit_button("Save Changes")

                    if update_btn:
                        if not updated_title.strip() or not updated_desc.strip():
                            st.warning("Both title and description are required.")
                        else:
                            # Check for duplicate title (excluding current JD)
                            duplicate = session.query(JobDescription).filter(
                                JobDescription.title == updated_title.strip(),
                                JobDescription.id != jd.id
                            ).first()
                            if duplicate:
                                st.error("Another JD with this title exists. Choose a different title.")
                            else:
                                jd.title = updated_title.strip()
                                jd.description = updated_desc.strip()
                                session.commit()
                                st.success(f"Updated Job Description '{updated_title.strip()}'")
                                st.session_state[f"edit_mode_{jd.id}"] = False
                                st.rerun()

            st.markdown("---")

            # Delete JD with confirmation checkbox
            if st.button(f"Delete '{jd.title}'", key=f"del_btn_{jd.id}"):
                st.session_state[f"confirm_del_{jd.id}"] = True

            if st.session_state.get(f"confirm_del_{jd.id}", False):
                confirm = st.checkbox(f"Confirm deletion of '{jd.title}' and all related evaluations", key=f"confirm_del_chk_{jd.id}")
                if confirm:
                    try:
                        session.delete(jd)  # This will cascade delete related evaluations if configured
                        session.commit()
                        st.success(f"Deleted Job Description '{jd.title}' and related evaluations.")
                        # Clean up session state and refresh UI
                        st.session_state.pop(f"confirm_del_{jd.id}", None)
                        st.session_state.pop(f"confirm_del_chk_{jd.id}", None)
                        st.rerun()
                    except Exception as e:
                        session.rollback()
                        st.error(f"Failed to delete JD: {e}")

    session.close()

elif view_option == "🧠 Evaluate":
    st.sidebar.header("🔍 ATS Evaluation")
    session = Session()
    jds = session.query(JobDescription).order_by(JobDescription.created_at.desc()).all()
    session.close()

    if not jds:
        st.warning("No job descriptions available. Please add one in 'Manage JDs' tab first.")
    else:
        jd_titles = [jd.title for jd in jds]
        selected_title = st.sidebar.selectbox("Select Job Description", jd_titles)
        jd_obj = next((jd for jd in jds if jd.title == selected_title), None)
        jd_text = jd_obj.description if jd_obj else ""

        name = st.sidebar.text_input("Candidate Name")
        email = st.sidebar.text_input("Candidate Email")
        uploaded_file = st.sidebar.file_uploader("Upload Resume (PDF)", type="pdf")
        run = st.sidebar.button("Evaluate")

        st.markdown("<h1 class='main-header'>📄 Smart ATS Management</h1>", unsafe_allow_html=True)
        st.write("Use AI to analyse and optimise your resume for a job description.")

        if run:
            if not uploaded_file or not jd_text.strip() or not name.strip() or not email.strip():
                st.warning("Please provide name, email, upload a resume and select a job description.")
            else:
                resume_text = input_pdf_text(uploaded_file)
                uploaded_file.seek(0)
                resume_binary = uploaded_file.read()

                session = Session()
                duplicate = session.query(EvaluationResult).filter_by(
                    resume_name=uploaded_file.name,
                    job_description_id=jd_obj.id
                ).first()

                if duplicate:
                    st.warning("⚠️ This resume has already been evaluated for the selected job description.")
                else:
                    with st.spinner("Analysing resume..."):
                        raw_output = get_ats_evaluation(resume_text, jd_text)
                        raw_output_clean = raw_output.replace("**", "").replace("```json", "").replace("```", "")
                        try:
                            raw_json = json.loads(raw_output_clean)
                        except json.JSONDecodeError:
                            st.error("⚠️ Failed to parse output. Showing raw response instead.")
                            raw_json = {"response": raw_output_clean}

                    score_str = raw_json.get("JD Match", "0%")
                    matched = raw_json.get("MatchedKeywords", [])
                    missing = raw_json.get("MissingKeywords", [])
                    summary = raw_json.get("Profile Summary", "No summary generated.")

                    session.add(EvaluationResult(
                        name=name.strip(),
                        email=email.strip(),
                        resume_name=uploaded_file.name,
                        resume_file=resume_binary,
                        job_description_id=jd_obj.id,
                        match_percent=score_str,
                        summary=summary,
                        matched_keywords=json.dumps(matched),
                        missing_keywords=json.dumps(missing)
                    ))
                    session.commit()
                    session.close()

                    st.success("✅ Evaluation saved successfully.")

                    tab1, tab2 = st.tabs(["📊 Result", "📄 Detailed View"])

                    with tab1:
                        st.subheader("📈 Match Score")
                        score = int(score_str.replace("%", "")) if "%" in score_str else 0
                        st.markdown(f"""
                            <div style='background-color: #28a745; color: white; font-size: 24px;
                                padding: 8px 16px; display: inline-block; border-radius: 6px; margin-bottom: 10px;'>
                                Match Score: {score}%
                            </div>
                        """, unsafe_allow_html=True)
                        st.progress(score)

                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("✅ Matched Keywords")
                            if isinstance(matched, list) and matched:
                                for item in matched:
                                    st.markdown(f"<span class='highlight'>{item.get('keyword', '')}</span>", unsafe_allow_html=True)
                            else:
                                st.write("No specific keywords matched.")

                        with col2:
                            st.subheader("❌ Missing Keywords")
                            if isinstance(missing, list) and missing:
                                for item in missing:
                                    st.markdown(f"<span class='highlight'>{item.get('keyword', '')}</span>", unsafe_allow_html=True)
                            else:
                                st.write("No major keywords missing. ✅")

                        st.subheader("🧾 Profile Summary")
                        st.write(summary)
                        st.download_button("⬇️ Download Summary", data=summary, file_name="profile_summary.txt")

                    with tab2:
                        st.subheader("📄 Detailed Output")

                        st.subheader("✅ Matched Keywords")
                        if isinstance(matched, list):
                            for item in matched:
                                st.markdown(f"<span class='highlight'>{item['keyword']}</span>: {item['reason']}", unsafe_allow_html=True)
                        else:
                            st.write("No matched keywords.")

                        st.subheader("❌ Missing Keywords")
                        if isinstance(missing, list):
                            for item in missing:
                                st.markdown(f"<span class='highlight'>{item['keyword']}</span>: {item['reason']}", unsafe_allow_html=True)
                        else:
                            st.write("No missing keywords.")

                        st.subheader("🧾 Profile Summary")
                        st.write(summary)

# History View with expandable cards and large, clear headers
elif view_option == "📜 History":
    st.markdown("<h2 class='main-header'>📜 Previous Evaluations</h2>", unsafe_allow_html=True)
    session = Session()
    jds = session.query(JobDescription).order_by(JobDescription.created_at.desc()).all()

    if not jds:
        st.info("No job descriptions found. Please add some in 'Manage JDs' tab.")
        session.close()
    else:
        jd_titles = [jd.title for jd in jds]
        selected_title = st.selectbox("Filter by Job Description", ["All"] + jd_titles)

        if selected_title == "All":
            evaluations = session.query(EvaluationResult).options(joinedload(EvaluationResult.job_description_rel)).order_by(EvaluationResult.created_at.desc()).all()
        else:
            jd_obj = next((jd for jd in jds if jd.title == selected_title), None)
            if jd_obj:
                evaluations = session.query(EvaluationResult).options(joinedload(EvaluationResult.job_description_rel))\
                    .filter_by(job_description_id=jd_obj.id).order_by(EvaluationResult.created_at.desc()).all()
            else:
                evaluations = []

        session.close()

        sort_option = st.selectbox("Sort by", ["Most Recent", "Highest Match", "Lowest Match"])
        search_text = st.text_input("🔍 Search Summary Keywords")

        if sort_option == "Most Recent":
            evaluations.sort(key=lambda r: r.created_at, reverse=True)
        elif sort_option == "Highest Match":
            evaluations.sort(key=lambda r: int(r.match_percent.replace('%', '').strip()) if r.match_percent else 0, reverse=True)
        elif sort_option == "Lowest Match":
            evaluations.sort(key=lambda r: int(r.match_percent.replace('%', '').strip()) if r.match_percent else 0)

        if search_text:
            evaluations = [row for row in evaluations if search_text.lower() in (row.summary or "").lower()]

        if evaluations:
            for row in evaluations:
                london_time = row.created_at.replace(tzinfo=datetime.timezone.utc).astimezone(pytz.timezone('Europe/London'))
                resume_b64 = base64.b64encode(row.resume_file).decode('utf-8')
                href = f'<a href="data:application/pdf;base64,{resume_b64}" download="{row.resume_name}">📂 Download Resume</a>'
                file_size_kb = round(len(row.resume_file) / 1024, 2)

                expander_label = (
                    f"{row.name or 'N/A'} | {row.email or 'N/A'} | JD: {row.job_description_rel.title} | "
                    f"Score: {row.match_percent} | {london_time.strftime('%Y-%m-%d %H:%M')}"
                )

                with st.expander(expander_label, expanded=False):
                    st.markdown(f"""
                        <div class="evaluation-field"><span class="evaluation-label">Candidate Name:</span> {row.name or 'N/A'}</div>
                        <div class="evaluation-field"><span class="evaluation-label">Email:</span> {row.email or 'N/A'}</div>
                        <div class="evaluation-field"><span class="evaluation-label">Resume:</span> {row.resume_name} ({file_size_kb} KB) {href}</div>
                        <div class="evaluation-field"><span class="evaluation-label">Job Description:</span> {row.job_description_rel.title}</div>
                        <div class="evaluation-field"><span class="evaluation-label">Evaluation Date:</span> {london_time.strftime('%Y-%m-%d %H:%M')}</div>
                        <div class="evaluation-field"><span class="evaluation-label">Match Score:</span> {row.match_percent}</div>
                        <div class="evaluation-field"><span class="evaluation-label">Summary:</span> {row.summary}</div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No evaluations found for this filter.")

elif view_option == "📈 Candidate Ranking":
    st.markdown("<h2 class='main-header'>📈 Candidate Ranking by Job Description</h2>", unsafe_allow_html=True)
    session = Session()
    jds = session.query(JobDescription).order_by(JobDescription.created_at.desc()).all()

    if not jds:
        st.info("No job descriptions found.")
    else:
        jd_titles = [jd.title for jd in jds]
        selected_title = st.selectbox("Select Job Description", jd_titles)
        jd_obj = next((jd for jd in jds if jd.title == selected_title), None)

        if jd_obj:
            evaluations = sorted(
                jd_obj.evaluations,
                key=lambda x: int(x.match_percent.replace('%', '').strip()) if x.match_percent else 0,
                reverse=True
            )

            if not evaluations:
                st.info("No evaluations found for the selected job description.")
            else:
                # Prepare data for display and plot
                data = []
                for rank, e in enumerate(evaluations, start=1):
                    data.append({
                        "Rank": rank,
                        "Name": e.name or "N/A",
                        "Email": e.email or "N/A",
                        "MatchPercent": int(e.match_percent.replace('%', '').strip()) if e.match_percent else 0,
                        "Summary": e.summary or "",
                        "ResumeLink": get_resume_download_link(e)
                    })

                df = pd.DataFrame(data)

                # Plot bar chart for match percentages
                st.subheader(f"📊 Match Percentage Distribution for '{selected_title}'")
                st.bar_chart(df.set_index("Name")["MatchPercent"])

                # Custom CSS for candidate cards and expander headers
                st.markdown("""
                    <style>
                        
                    </style>
                """, unsafe_allow_html=True)

                st.write(f"### Candidate Rankings for '{selected_title}':")
                
                for row in data:
                    expander_label = f"🏅 Rank #{row['Rank']} — 👤 {row['Name']} — ✉️ {row['Email']} — ⭐ {row['MatchPercent']}%"
                    with st.expander(expander_label, expanded=False):
                        st.markdown(f"""
                            <div class="candidate-field"><span class="candidate-label">Name:</span> {row['Name']}</div>
                            <div class="candidate-field"><span class="candidate-label">Email:</span> {row['Email']}</div>
                            <div class="candidate-field"><span class="candidate-label">Match Score:</span> {row['MatchPercent']}%</div>
                            <div class="candidate-field"><span class="candidate-label">Summary:</span> {row['Summary']}</div>
                            <div class="candidate-field">{row['ResumeLink']}</div>
                        """, unsafe_allow_html=True)

                export_df = df.drop(columns=["ResumeLink"])
                st.download_button("📥 Export Ranked Candidates as CSV", export_df.to_csv(index=False), "ranked_candidates.csv")

    session.close()
