import streamlit as st
import requests
import uuid
import os
from dotenv import load_dotenv

# =====================================================================
# 1. LOAD ENVIRONMENT CONFIGURATION
# =====================================================================
load_dotenv()

backend_host = os.getenv("BACKEND_HOST", "localhost")
backend_port = os.getenv("API_PORT", "8005")

if backend_host == "0.0.0.0":
    backend_host = "localhost"

BACKEND_URL = f"http://{backend_host}:{backend_port}/chat"


# =====================================================================
# 2. STREAMLIT PAGE CONFIGURATION & STYLING
# =====================================================================
st.set_page_config(
    page_title="AI Page Summarizer & Insights",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling to make the interface look modern and premium
st.markdown("""
<style>
    .header-title {
        background: linear-gradient(135deg, #FF4B4B, #FF8F8F, #4A90E2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0px;
        padding-bottom: 5px;
    }
    .header-subtitle {
        color: #8892b0;
        font-size: 1.1rem;
        margin-top: 0px;
        margin-bottom: 30px;
    }
    [data-testid="stSidebar"] {
        background-color: #11151c;
        border-right: 1px solid #1e293b;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #FF4B4B 0%, #FF6B6B 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(255, 75, 75, 0.3);
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF4B4B 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(255, 75, 75, 0.5);
    }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# 3. INITIALIZE STATE (MEMORY)
# =====================================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# State variables to hold values from the sidebar form during re-runs
if "pending_email" not in st.session_state:
    st.session_state.pending_email = None

if "pending_url" not in st.session_state:
    st.session_state.pending_url = None

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 Hello! I am your AI Web Summarizer Assistant.\n\n"
                "I can analyze any webpage URL you provide and email you a summary and key insights "
                "directly to your inbox using our n8n automation workflow.\n\n"
                "👉 Use the **Sidebar Form** to quickly trigger the workflow, or type a request directly in the chat below!"
            )
        }
    ]


# =====================================================================
# 4. BACKEND COMMUNICATION HELPER
# =====================================================================
# We updated this function to take 'email' and 'url' and pass them to the backend API.
def send_message_to_backend(message_text: str, email: str = None, url: str = None) -> str:
    """
    Sends a message, email, and URL to the FastAPI backend and returns the response.
    """
    payload = {
        "session_id": st.session_state.session_id,
        "message": message_text
    }
    
    # Only include email and article_url if they are actually provided
    if email:
        payload["email"] = email
    if url:
        payload["article_url"] = url
    
    try:
        response = requests.post(BACKEND_URL, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict):
                if "output" in data:
                    return str(data["output"])
                elif "response" in data:
                    return str(data["response"])
                elif "message" in data:
                    return str(data["message"])
                elif "detail" in data:
                    return str(data["detail"])
                else:
                    return f"Workflow completed! Response data:\n```json\n{data}\n```"
            elif isinstance(data, list):
                if len(data) > 0:
                    return str(data[0])
                return "Workflow completed with empty response list."
            else:
                return str(data)
        else:
            return f"❌ Error: Backend returned status code {response.status_code}. Details: {response.text}"
            
    except requests.exceptions.ConnectionError:
        return (
            "❌ Connection Error: Could not connect to the FastAPI backend.\n\n"
            f"Please verify that your backend server is running at **{BACKEND_URL}**!"
        )
    except Exception as e:
        return f"❌ Unexpected Error occurred: {str(e)}"


# =====================================================================
# 5. USER INTERFACE (UI) LAYOUT
# =====================================================================
st.markdown('<div class="header-title">Web Summarizer & Insights AI</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">Analyze any web page and receive a summary in your email</div>', unsafe_allow_html=True)

# --- SIDEBAR: QUICK FORM INPUTS ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">⚙️ Quick Inputs</div>', unsafe_allow_html=True)
    st.write("Fill in the fields below to quickly run the email insight workflow.")
    
    url_input = st.text_input(
        "🔗 Web Page URL:",
        placeholder="https://example.com/article-to-summarize"
    )
    
    email_input = st.text_input(
        "📧 Recipient Email:",
        placeholder="your-email@gmail.com"
    )
    
    submit_button = st.button("Generate Summary & Email 🚀")

# --- MAIN AREA: DISPLAY CHAT HISTORY ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


# =====================================================================
# 6. ACTION HANDLERS
# =====================================================================

# CASE A: If the user clicked the sidebar run button
if submit_button:
    if not url_input:
        st.sidebar.error("⚠️ Please enter a Web Page URL!")
    elif not email_input:
        st.sidebar.error("⚠️ Please enter a Recipient Email!")
    else:
        # Save inputs into session state so they persist across the reload
        st.session_state.pending_email = email_input
        st.session_state.pending_url = url_input
        
        # Display the action in the chat
        formatted_message = f"Please summarize this webpage: {url_input} and send the insights to this email: {email_input}"
        st.session_state.messages.append({"role": "user", "content": formatted_message})
        st.rerun()

# CASE B: If the user typed a manual message in the chat input
user_chat_input = st.chat_input("Type your message here...")
if user_chat_input:
    st.session_state.messages.append({"role": "user", "content": user_chat_input})
    st.rerun()

# --- RUNNING THE BACKEND REQUEST ---
if st.session_state.messages[-1]["role"] == "user":
    last_user_message = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant"):
        with st.spinner("⏳ Analyzing webpage and triggering email workflow... Please wait."):
            # Send the request to backend (passing pending form values if any)
            response_text = send_message_to_backend(
                last_user_message,
                email=st.session_state.pending_email,
                url=st.session_state.pending_url
            )
            
            # Clear the pending variables so they don't get reused on next message
            st.session_state.pending_email = None
            st.session_state.pending_url = None
            
            st.write(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.rerun()

