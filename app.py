import streamlit as st
import requests
import docx2txt
import PyPDF2
import re

# Initialize DeepSeek API key from Streamlit Secrets
DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]

def query_deepseek(prompt: str, model="deepseek-chat"):
    """Query DeepSeek API with error handling"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
        return None

def extract_text_from_file(uploaded_file):
    """Extract text from PDF/DOCX files with error handling"""
    try:
        if uploaded_file.type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            text = " ".join(page.extract_text() for page in reader.pages if page.extract_text())
        elif uploaded_file.type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword"
        ]:
            text = docx2txt.process(uploaded_file)
        else:
            text = uploaded_file.read().decode("utf-8")
        return text.strip()
    except Exception as e:
        st.error(f"Failed to process file: {str(e)}")
        return ""

def analyze_resume(resume_text: str, jd_text: str):
    """Generate analysis prompt for DeepSeek"""
    prompt = f"""
    Analyze this resume against the job description and provide:
    
    1. Fit Score (0-100) with brief justification
    2. Top 3 matching skills with experience evidence
    3. Top 3 missing qualifications
    4. Summary (3-4 sentences) with overall assessment
    
    ---JOB DESCRIPTION---\n{jd_text}\n---
    ---RESUME---\n{resume_text}\n---
    """
    return query_deepseek(prompt)

# Streamlit UI Configuration
st.set_page_config(
    page_title="AI Resume Matcher (DeepSeek)",
    page_icon="🔍",
    layout="wide"
)

# Main App Interface
st.title("🔍 AI-Powered Resume Matcher")
st.caption("Powered by DeepSeek AI | Upload a resume and job description for analysis")

with st.form("analysis_form"):
    col1, col2 = st.columns(2)
    with col1:
        jd_text = st.text_area("Job Description", height=250, 
                             placeholder="Paste the job description here...")
    with col2:
        resume_file = st.file_uploader("Upload Resume", 
                                    type=["pdf", "docx", "txt"],
                                    help="Supports PDF, DOCX, and TXT formats")
    
    submitted = st.form_submit_button("Analyze Resume", type="primary")

# Analysis Execution
if submitted:
    if not jd_text:
        st.warning("Please enter a job description")
    elif not resume_file:
        st.warning("Please upload a resume file")
    else:
        with st.spinner("Analyzing resume with DeepSeek AI..."):
            resume_text = extract_text_from_file(resume_file)
            if resume_text:
                analysis_result = analyze_resume(resume_text, jd_text)
                
                if analysis_result:
                    st.success("Analysis Complete!")
                    st.divider()
                    
                    # Display Results
                    st.subheader("📊 Evaluation Results")
                    
                    # Extract and display score
                    score_match = re.search(r"1\. Fit Score: (\d+)", analysis_result)
                    if score_match:
                        score = int(score_match.group(1))
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Match Score", f"{score}/100")
                        with col2:
                            st.metric("Resume Length", f"{len(resume_text.split())} words")
                    
                    # Formatted analysis
                    st.markdown(analysis_result.replace("1.", "### 1.")
                                              .replace("2.", "### 2.")
                                              .replace("3.", "### 3.")
                                              .replace("4.", "### 4."))
                    
                    # Debug section
                    with st.expander("🔍 View extracted resume text"):
                        st.text(resume_text[:2000] + ("..." if len(resume_text) > 2000 else ""))
