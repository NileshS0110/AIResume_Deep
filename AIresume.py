import streamlit as st
import requests
import docx2txt
import PyPDF2
import os
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# DeepSeek API function
def query_deepseek(prompt: str, model="deepseek-chat"):
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
            "https://api.deepseek.com/v1/chat/completions",  # Verify endpoint
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# File text extraction
def extract_text_from_file(uploaded_file):
    try:
        if uploaded_file.type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            text = " ".join(page.extract_text() for page in reader.pages if page.extract_text())
        elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            text = docx2txt.process(uploaded_file)
        else:
            text = uploaded_file.read().decode("utf-8")
        return text.strip()
    except Exception as e:
        st.error(f"File processing error: {str(e)}")
        return ""

# Evaluation function
def evaluate_with_deepseek(resume_text: str, jd_text: str):
    prompt = f"""
    Analyze this resume against the job description and provide:
    
    1. Fit Score (0-100) with justification
    2. Top 3 matching skills
    3. Top 3 missing qualifications
    4. Summary (3-4 sentences)
    
    ---JOB DESCRIPTION---\n{jd_text}\n---
    ---RESUME---\n{resume_text}\n---
    """
    return query_deepseek(prompt)

# Streamlit UI
st.set_page_config(page_title="Resume Matcher AI", layout="wide")
st.title("🚀 Resume Matcher (DeepSeek AI)")
st.markdown("Upload a resume and job description to evaluate candidate fit.")

with st.form("eval_form"):
    jd = st.text_area("Paste Job Description", height=200)
    resume_file = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"])
    submitted = st.form_submit_button("Evaluate")

if submitted:
    if jd and resume_file:
        with st.spinner("Analyzing..."):
            resume_text = extract_text_from_file(resume_file)
            if resume_text:
                result = evaluate_with_deepseek(resume_text, jd)
                
                if result:
                    st.success("Analysis Complete!")
                    st.subheader("📊 Results")
                    
                    # Extract score using regex
                    score_match = re.search(r"1\. Fit Score: (\d+)", result)
                    if score_match:
                        score = int(score_match.group(1))
                        st.metric("Match Score", f"{score}/100")
                    
                    st.markdown(result.replace("1.", "### 1.").replace("2.", "### 2."))
                    
                    # Show raw text (debug)
                    with st.expander("View Extracted Resume Text"):
                        st.text(resume_text[:2000] + "...")
    else:
        st.error("Please provide both a job description and resume file.")
