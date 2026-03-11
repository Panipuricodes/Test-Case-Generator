import streamlit as st
import spacy
import pandas as pd
import PyPDF2
import docx
from docx import Document
import io
import os
import speech_recognition as sr

# Load the pre-installed NLP model
nlp = spacy.load("en_core_web_sm")
# -------------------------------
# NEW: Extract Text from PDF (Fixes your error)
# -------------------------------
def extract_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

# -------------------------------
# Voice to Text Function (Safe)
# -------------------------------
def voice_to_text():
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("🎙️ Speak now...")
            audio = recognizer.listen(source)

        text = recognizer.recognize_google(audio)
        return text
    except Exception as e:
        return f"Voice input not supported: {e}"

# -------------------------------
# Extract Text from DOCX
# -------------------------------
def extract_docx(file):
    doc = Document(file)
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text)
    return "\n".join(full_text)

# -------------------------------
# NLP Extraction (Improved)
# -------------------------------
def extract_requirements(text):
    doc = nlp(text)
    actions = set()
    inputs = set()

    for token in doc:
        if token.pos_ == "VERB":
            actions.add(token.lemma_.lower())
        if token.pos_ == "NOUN":
            inputs.add(token.lemma_.lower())

    return list(actions), list(inputs)

# -------------------------------
# Requirement Classification
# -------------------------------
def classify_requirement(text):
    text = text.lower()
    if "performance" in text:
        return "Non-Functional - Performance"
    elif "security" in text:
        return "Non-Functional - Security"
    elif "usability" in text:
        return "Non-Functional - Usability"
    else:
        return "Functional Requirement"

# -------------------------------
# Test Case Generator (Improved)
# -------------------------------
def generate_test_cases(text):
    text = text.lower()
    test_cases = []

    if "login" in text:
        test_cases.extend([
            "Verify login with valid credentials",
            "Verify error for invalid email format",
            "Verify login with empty password",
            "Verify login with incorrect password",
            "Verify login with SQL injection attempt"
        ])

    if "register" in text or "signup" in text:
        test_cases.extend([
            "Verify registration with valid details",
            "Verify registration with existing email",
            "Verify weak password rejection",
            "Verify registration with empty fields"
        ])

    if "password" in text:
        test_cases.extend([
            "Verify password below minimum length",
            "Verify password at minimum length",
            "Verify password exceeding maximum length"
        ])

    if "upload" in text:
        test_cases.extend([
            "Verify upload with valid file format",
            "Verify upload with invalid file format",
            "Verify upload exceeding file size limit"
        ])

    if "search" in text:
        test_cases.extend([
            "Verify search with valid keyword",
            "Verify search with empty input",
            "Verify search with special characters"
        ])

    if not test_cases:
        test_cases.extend([
            "Verify system with valid input",
            "Verify system with invalid input"
        ])

    return list(set(test_cases))

# -------------------------------
# Assign Smart Priority
# -------------------------------
def assign_priority(test_cases):
    priorities = []
    for tc in test_cases:
        if any(word in tc.lower() for word in ["invalid", "error", "sql", "exceed", "empty"]):
            priorities.append("High")
        else:
            priorities.append("Medium")
    return priorities

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="AI Test Case Generator", layout="wide")

st.title("Test Case Generator")
st.markdown("Upload SRS document or use Voice Input to generate test cases automatically.")

# Sidebar
st.sidebar.header("Input Options")
input_method = st.sidebar.radio("Choose Input Method:", ["Upload SRS File", "Voice Input"])

text_data = ""

# -------------------------------
# File Upload
# -------------------------------
if input_method == "Upload SRS File":
    uploaded_file = st.file_uploader("Upload SRS File", type=["txt", "docx", "pdf", "py", "js"])

    if uploaded_file is not None:
        if uploaded_file.name.endswith(".txt"):
            text_data = uploaded_file.read().decode("utf-8")
        elif uploaded_file.name.endswith(".docx"):
            text_data = extract_docx(uploaded_file)
        elif uploaded_file.name.endswith(".pdf"):
            text_data = extract_pdf(uploaded_file) # Now defined!
        elif uploaded_file.name.endswith(".py"): 
            text_data =  uploaded_file.read().decode("utf-8")
        else:
            st.error("Unsupported file format")

# -------------------------------
# Voice Input
# -------------------------------
if input_method == "Voice Input":
    if st.button("🎙️ Record Requirement"):
        text_data = voice_to_text()

# -------------------------------
# Display & Process Text
# -------------------------------
if text_data:
    st.subheader("📄 Extracted Requirement Text")
    st.text_area("Requirement:", text_data, height=200)

    st.subheader("📌 Requirement Type")
    st.write(classify_requirement(text_data))

    actions, inputs = extract_requirements(text_data)

    st.subheader("🔍 NLP Analysis")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Detected Actions (Verbs):")
        st.write(actions)
    with col2:
        st.write("Detected Inputs (Nouns):")
        st.write(inputs)

    test_cases = generate_test_cases(text_data)
    priorities = assign_priority(test_cases)

    st.subheader("🧪 Generated Test Cases")
    st.metric("Total Test Cases Generated", len(test_cases))

    df = pd.DataFrame({
        "TC_ID": [f"TC_{i+1}" for i in range(len(test_cases))],
        "Test_Case_Description": test_cases,
        "Priority": priorities
    })

    st.dataframe(df, use_container_width=True)

    # Download Button (Note: Requires openpyxl for Excel export)
    buffer = io.BytesIO()
    try:
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button(
            label="📥 Download Test Cases as Excel",
            data=buffer.getvalue(),
            file_name="Generated_Test_Cases.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except ImportError:
        st.warning("Please install 'openpyxl' to download Excel files.")


st.success("Project Ready for Final Year Submission 🚀")