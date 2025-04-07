import streamlit as st
from deepseek_api import DeepSeekAPI  # Assuming you have a DeepSeek API client
import docx2txt
import PyPDF2
import io
import os

# Set your DeepSeek API key here or load from environment variable
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
deepseek = DeepSeekAPI(api_key=DEEPSEEK_API_KEY)

def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        reader = PyPDF2.PdfReader(uploaded_file)
        text = " ".join(page.extract_text() for page in reader.pages if page.extract_text())
    elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        text = docx2txt.process(uploaded_file)
    else:
        text = uploaded_file.read().decode("utf-8")
    return text

def evaluate_with_deepseek(resume_text: str, jd_text: str):
    prompt = f"""
    Job Description:
    {jd_text}

    Candidate Resume:
    {resume_text}

    Based on the job description and the candidate's resume, provide:
    1. A Fit Score out of 100.
    2. A 3-4 sentence summary highlighting key relevant experience and potential gaps.
    3. Key skills from the resume that match the job description.
    4. Potential concerns or missing qualifications.
    """

    response = deepseek.generate(
        model="deepseek-chat",  # Use the appropriate DeepSeek model
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

st.set_page_config(page_title="RecruitAI Copilot", layout="wide")
st.title("RecruitAI Copilot – Resume Matcher")

st.markdown("""
Upload a candidate resume and input a job description to evaluate the fit using AI.
""")

with st.form("resume_form"):
    jd_input = st.text_area("Job Description", height=200)
    uploaded_resume = st.file_uploader("Upload Candidate Resume (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
    submitted = st.form_submit_button("Evaluate")

if submitted:
    if jd_input and uploaded_resume:
        resume_text = extract_text_from_file(uploaded_resume)
        with st.spinner("Analyzing with DeepSeek AI..."):
            ai_output = evaluate_with_deepseek(resume_text, jd_input)

        st.subheader("AI Evaluation Result")
        st.success(ai_output)
        
        # Add additional visualization
        st.markdown("### Key Metrics")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Resume Length", f"{len(resume_text.split())} words")
        with col2:
            # Extract score if possible (this is a simple regex approach)
            import re
            match = re.search(r"Fit Score: (\d+) out of 100", ai_output)
            if match:
                score = int(match.group(1))
                st.metric("Match Score", f"{score}/100")
    else:
        st.error("Please upload a resume file and enter a job description.")
