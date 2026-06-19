from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os
import re
from pathlib import Path
from dotenv import load_dotenv

# =====================================================================
# 1. ENVIRONMENT CONFIGURATION
# =====================================================================
current_dir = Path(__file__).resolve().parent
dotenv_path = current_dir / ".env"
if not dotenv_path.exists():
    dotenv_path = current_dir.parent / ".env"

load_dotenv(dotenv_path=dotenv_path)

app = FastAPI(title="Module 21 Assignment Backend")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if WEBHOOK_URL:
    print(f"✅ Webhook URL loaded: {WEBHOOK_URL}")
else:
    print("⚠️ WARNING: WEBHOOK_URL not found in environment variables! Please check your .env file.")


# =====================================================================
# 2. INPUT DATA MODEL & HELPER FUNCTIONS
# =====================================================================
# We updated the model to accept 'email' and 'article_url' directly from the frontend.
class ChatRequest(BaseModel):
    session_id: str
    message: str | None = None
    email: str | None = None
    article_url: str | None = None


def extract_url_and_email(text: str):
    """
    Helper function to search for an email and a URL in a text message
    using Regular Expressions (regex). This serves as a fallback 
    if the user types them manually in the chat input.
    """
    email = None
    url = None
    
    # 1. Extract email: matches text like 'name@domain.com'
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_match:
        email = email_match.group(0)
        
    # 2. Extract URL: matches text starting with http:// or https://
    url_match = re.search(r'https?://[^\s]+', text)
    if url_match:
        url = url_match.group(0)
        
    return url, email


# =====================================================================
# 3. CHAT ENDPOINT (WEBHOOK ROUTER)
# =====================================================================
@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Endpoint that receives chat queries, resolves 'email' and 'article_url',
    and forwards the correct keys to the n8n Webhook.
    """
    if not WEBHOOK_URL:
        return {
            "status": "error",
            "detail": "WEBHOOK_URL is missing. Please add it to your .env file."
        }

    # Resolve email and URL. If they aren't passed directly as keys,
    # try to extract them from the free-form text 'message' using our regex helper.
    email = request.email
    article_url = request.article_url
    
    if not email or not article_url:
        extracted_url, extracted_email = extract_url_and_email(request.message)
        if not email:
            email = extracted_email
        if not article_url:
            article_url = extracted_url

    # Construct the JSON payload that n8n expects
    payload = {
        "session_id": request.session_id,
        "message": request.message,
        "email": email,
        "article_url": article_url
    }
    
    print(f"\n📨 Forwarding to n8n Webhook: {payload}")

    # Set up client timeout (120 seconds for n8n scrapers and LLMs to finish)
    timeout_config = httpx.Timeout(120.0, connect=10.0)
    
    async with httpx.AsyncClient(timeout=timeout_config) as client:
        try:
            response = await client.post(WEBHOOK_URL, json=payload)
            response.raise_for_status()

            print(f"✅ n8n responded with status code: {response.status_code}")

            try:
                response_json = response.json()
                print(f"📦 Response JSON: {response_json}")
                return response_json
            except (ValueError, TypeError):
                # Fallback if n8n returns raw text
                print(f"📝 Response Text: {response.text}")
                return {"response": response.text}

        except httpx.HTTPStatusError as e:
            error_msg = f"n8n returned HTTP error: {e.response.status_code} - {e.response.text}"
            print(f"❌ {error_msg}")
            return {"status": "error", "detail": error_msg}
            
        except httpx.TimeoutException:
            error_msg = "Connection timed out. The n8n workflow took longer than 120 seconds to respond."
            print(f"❌ {error_msg}")
            return {"status": "error", "detail": error_msg}
            
        except Exception as e:
            error_msg = f"Network or connection error: {str(e)}"
            print(f"❌ {error_msg}")
            return {"status": "error", "detail": error_msg}


# =====================================================================
# 4. RUNNER
# =====================================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8005))
    uvicorn.run(app, host="0.0.0.0", port=port)