import os
import streamlit as st
import PyPDF2
import google.generativeai as genai
import time
import random

# Set up Google Gemini API Key
GEMINI_API_KEY = "AIzaSyCJrs0gkZJbZ9mr3Mf570pHPTU7ELI5iNs"  # Replace with your actual API key or use Streamlit Secrets
genai.configure(api_key=GEMINI_API_KEY)

# Streamlit UI
st.set_page_config(page_title="AI Personal Finance Assistant", page_icon="💰", layout="wide")

# Custom CSS for Styling
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        font-size: 34px;
        font-weight: bold;
        color: #4CAF50;
        text-shadow: 2px 2px 5px rgba(76, 175, 80, 0.4);
    }
    .sub-title {
        text-align: center;
        font-size: 18px;
        color: #ddd;
        margin-bottom: 20px;
    }
    .stButton button {
        background: linear-gradient(to right, #4CAF50, #388E3C);
        color: white;
        font-size: 18px;
        padding: 10px 20px;
        border-radius: 8px;
        transition: 0.3s;
    }
    .stButton button:hover {
        background: linear-gradient(to right, #388E3C, #2E7D32);
    }
    .result-card {
        background: rgba(0, 150, 136, 0.1);
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        box-shadow: 0px 2px 8px rgba(0, 150, 136, 0.2);
    }
    .success-banner {
        background: linear-gradient(to right, #2E7D32, #1B5E20);
        color: white;
        padding: 15px;
        font-size: 18px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin-top: 15px;
        box-shadow: 0px 2px 8px rgba(0, 150, 136, 0.5);
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar with usage info
st.sidebar.title("ℹ️ How to Use This Tool?")
st.sidebar.write("- Upload your Paytm Transaction History PDF.")
st.sidebar.write("- The AI will analyze your transactions.")
st.sidebar.write("- You will receive financial insights including income, expenses, savings, and spending trends.")
st.sidebar.write("- Use this data to plan your finances effectively.")

st.markdown('<h1 class="main-title">💰 AI-Powered Personal Finance Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Upload your Paytm Transaction History PDF for Financial Insights</p>', unsafe_allow_html=True)

# Upload PDF File
uploaded_file = st.file_uploader("📂 Upload PDF File", type=["pdf"], help="Only PDF files are supported")

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file using PyPDF2."""
    text = ""
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"❌ PDF Extraction Error: {e}")
        return None

def analyze_financial_data(text, max_retries=3, initial_delay=1, max_delay=5):
    """Sends extracted text to Google Gemini AI for financial insights with retry logic."""
    model = genai.GenerativeModel("learnlm-1.5-pro-experimental")
    prompt = f"""
    Analyze the following Paytm transaction history and generate financial insights:
    {text}
    Provide a detailed breakdown in the following format:
    **Financial Insights for [User Name]**
    **Key Details:**
    - **Overall Monthly Income & Expenses:**
      - Month: [Month]
      - Income: ₹[Amount]
      - Expenses: ₹[Amount]
    - **Unnecessary Expenses Analysis:**
      - Expense Category: [Category Name]
      - Amount: ₹[Amount]
      - Recommendation: [Suggestion]
    - **Savings Percentage Calculation:**
      - Savings Percentage: [Percentage] %
    - **Expense Trend Analysis:**
      - Notable Trends: [Trend Details]
    - **Cost Control Recommendations:**
      - Suggestion: [Detailed Suggestion]
    - **Category-Wise Spending Breakdown:**
      - Category: [Category Name] - ₹[Amount]
    """
    for i in range(max_retries):
        try:
            response = model.generate_content(prompt)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.text.strip() if response else "⚠️ Error processing financial data."
        except Exception as e:
            print(f"Error during AI analysis (attempt {i+1}/{max_retries}): {e}")
            if i < max_retries - 1:
                delay = min(initial_delay * (2 ** i) + random.random(), max_delay)
                print(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            else:
                st.error("⚠️ AI analysis failed after multiple retries. Please try again later or with a different document.")
                return None
    return None

def generate_insights_with_retry(prompt, max_retries=3, delay_range=(2, 5)):
    """Uses Gemini API to generate insights with retry mechanism."""
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            st.warning(f"Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                sleep_time = random.uniform(*delay_range)
                time.sleep(sleep_time)
            else:
                st.error("🚫 Analysis failed after several attempts.")
                return None


# Main Logic
if uploaded_file is not None:
    temp_path = f"temp_{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())

    st.success("✅ File uploaded!")

    with st.spinner("📖 Extracting text..."):
        raw_text = extract_text_from_pdf(temp_path)

    if raw_text:
        prompt = f"""
        Analyze the following transaction data and return a structured personal finance summary:

        {raw_text}

        Format:
        - Monthly Summary
        - Income vs Expenses
        - Savings Rate
        - Top Spending Categories
        - Redundant or Unnecessary Expenses
        - Suggestions for Better Budgeting
        """

        with st.spinner("🧠 Gemini is analyzing your financial data..."):
            insights = generate_insights_with_retry(prompt)

        if insights:
            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            st.subheader("📈 Financial Analysis Report")
            st.write(insights)
            st.markdown('</div>', unsafe_allow_html=True)
            st.balloons()
    else:
        st.error("📄 Could not extract text from this PDF. Make sure it's not a scanned image.")

    os.remove(temp_path)
