import os
import copy
import requests
from responses import custom_responses as SHARED_CUSTOM_RESPONSES
from dotenv import load_dotenv
import streamlit as st  # ensure st is available for page config
import webbrowser  # Import webbrowser module

load_dotenv()
# Do NOT prefill the UI with the key. Keep default empty so the key is never shown.
DEFAULT_KEY = "" 

# --- Page config + dark theme CSS ---
st.set_page_config(page_title="Alpha AI — Dark", layout="wide", initial_sidebar_state="expanded")

DARK_CSS = """
<style>
:root{--bg:#0f1720;--card:#0f1725;--accent:#7c3aed;--muted:#9ca3af;--user:#06b6d4;}
body { background-color: var(--bg); color: #e5e7eb; }
.stApp { background-color: var(--bg); color: #e5e7eb; }
.chat-wrap{max-width:980px;margin:18px auto;padding:18px;border-radius:12px;
           background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
           box-shadow: 0 8px 30px rgba(2,6,23,0.6);}
.chat-list{max-height:64vh;overflow:auto;padding:8px;}
.msg{padding:10px 14px;border-radius:12px;margin:8px 0;display:inline-block;max-width:78%;}
.msg.ai{background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border:1px solid rgba(255,255,255,0.03); color:#e6eef8;}
.msg.user{background:linear-gradient(90deg,var(--user),var(--accent)); color:#fff; float:right;}
.clear{clear:both;}
.input-row{display:flex;gap:8px;margin-top:12px;align-items:center;}
.input-text{flex:1;padding:10px;border-radius:10px;border:1px solid rgba(255,255,255,0.04);
           background:transparent;color:inherit;}
.send-btn{background:var(--accent);color:white;padding:8px 12px;border-radius:10px;border:none;cursor:pointer;}
.small{font-size:12px;color:var(--muted);margin-top:6px;}
.sidebar .stTextInput>div>div>input{background:transparent;color:inherit;border:1px solid rgba(255,255,255,0.04)}

/* Style the Streamlit 'Send' button specifically (uses aria-label attribute) */
button[aria-label="Send"]{
  background:#000 !important;
  color:#fff !important;
  border-radius:10px !important;
  padding:8px 12px !important;
  border:none !important;
  cursor:pointer !important;
  transition: transform .25s ease, background-color .35s ease, box-shadow .25s ease;
  box-shadow: 0 6px 18px rgba(0,0,0,0.45);
}

/* Subtle lift on hover */
button[aria-label="Send"]:hover{
  transform: translateY(-3px);
}

/* Animate to pale red with a sliding effect when clicked (transient) */
button[aria-label="Send"]:active{
  animation: slideRed .45s forwards;
}

/* keyframes for sliding pale-red effect */
@keyframes slideRed{
  0%{
    background:#000;
    color:#fff;
    transform: translateX(0);
    box-shadow: 0 6px 18px rgba(0,0,0,0.45);
  }
  60%{
    background:#ffdfe0;
    color:#000;
    transform: translateX(10px);
    box-shadow: 0 8px 20px rgba(255,100,100,0.08);
  }
  100%{
    background:#ffdfe0;
    color:#000;
    transform: translateX(6px);
    box-shadow: 0 6px 14px rgba(255,100,100,0.06);
  }
}
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

# --- API call (same as your app.py) ---
def call_deepseek_api(question, api_key: str = None):
    # Use explicit api_key if provided; otherwise try session_state then .env (hidden)
    api_key = (api_key or st.session_state.get("api_key") or os.getenv("OPENROUTER_API_KEY", "")).strip()
    url = "https://openrouter.ai/api/v1/chat/completions"
    if not api_key:
        return {"error": "Missing API key. Enter it in Settings (sidebar) or set OPENROUTER_API_KEY in .env"}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "deepseek/deepseek-chat",
        "messages": [{"role": "user", "content": f"Question: {question}\nAnswer:"}],
        "temperature": 0.7,
        "max_tokens": 512
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
    except Exception as e:
        return {"error": f"Request failed: {e}"}
    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}: {r.text}"}
    return r.json()

# --- simple user type detection (copied/simplified) ---
def detect_user_type(question):
    q = question.lower()
    if any(w in q for w in ["what is", "how do i", "explain", "beginner", "new to"]):
        return "beginner"
    if any(w in q for w in ["algorithm", "optimization", "performance", "scalability"]):
        return "expert"
    if any(w in q for w in ["homework", "assignment", "study", "exam"]):
        return "student"
    if any(w in q for w in ["business", "project", "client", "deadline"]):
        return "professional"
    return "general"

# --- initial UI state ---
if "api_key" not in st.session_state:
    st.session_state.api_key = DEFAULT_KEY
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "ai", "content": "Hello! I'm Alpha AI — ask me anything."}]
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {"type": "general", "previous_questions": []}
if "custom_responses" not in st.session_state:
    # load shared responses from responses.py (deepcopy to avoid cross-module mutation)
    st.session_state.custom_responses = copy.deepcopy(SHARED_CUSTOM_RESPONSES)

# --- helpers ---
def get_custom_response(question):
    """Flexible matching: exact or containment; returns profile-specific answer if present."""
    q = question.lower().strip()
    # exact match
    if q in st.session_state.custom_responses:
        responses = st.session_state.custom_responses[q]
        utype = st.session_state.user_profile.get("type", "general")
        return responses.get(utype) or responses.get("general")
    # containment fallback
    for key, responses in st.session_state.custom_responses.items():
        if key in q or q in key:
            utype = st.session_state.user_profile.get("type", "general")
            return responses.get(utype) or responses.get("general")
    return None

def mask_key(key: str):
    if not key:
        return "(not set)"
    return key if len(key) <= 8 else f"{key[:4]}...{key[-4:]}"

# --- sidebar: settings ---
st.sidebar.title("Settings")
st.sidebar.text_input("OpenRouter API key", key="api_key", type="password")
# Only verify the key on demand; don't show the key or mask automatically in the UI
if st.sidebar.button("Test API key"):
    with st.spinner("Testing..."):
        probe = call_deepseek_api("ping", st.session_state.api_key)
        if "error" in probe:
            st.sidebar.error("Invalid key or request failed.")
        else:
            st.sidebar.success("API key looks valid.")

st.sidebar.markdown("---")
st.sidebar.selectbox("Profile type", options=["general","beginner","expert","student","professional","lover"], key="profile_select")
st.sidebar.checkbox("Auto-detect profile from messages", value=True, key="auto_detect_profile")
# keep UI selection in the profile state
st.session_state.user_profile["type"] = st.session_state.profile_select

# --- main chat UI (themed + interactive) ---
st.title("Alpha AI — Dark Chat")
with st.container():
    st.markdown("<div class='chat-wrap'>", unsafe_allow_html=True)
    st.markdown("<div class='chat-list'>", unsafe_allow_html=True)
    # render messages with CSS classes
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            html = f"<div class='msg user'>{msg['content']}</div><div class='clear'></div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            html = f"<div class='msg ai'>{msg['content']}</div><div class='clear'></div>"
            st.markdown(html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # define send_message before widgets
    def send_message():
        question = st.session_state.get("input_text", "").strip()
        if not question:
            return

        # append user message
        st.session_state.messages.append({"role": "user", "content": question})

        # profile auto-detect (only if enabled)
        detected = detect_user_type(question)
        if detected != "general" and st.session_state.get("auto_detect_profile", True):
            st.session_state.user_profile["type"] = detected

        # track history
        st.session_state.user_profile.setdefault("previous_questions", []).append(question)
        if len(st.session_state.user_profile["previous_questions"]) > 20:
            st.session_state.user_profile["previous_questions"] = st.session_state.user_profile["previous_questions"][-20:]

        # custom response check
        custom = get_custom_response(question)
        if custom:
            st.session_state.messages.append({"role": "ai", "content": custom})
            st.session_state.input_text = ""
            return

        # call API
        with st.spinner("Alpha is thinking..."):
            result = call_deepseek_api(question, st.session_state.api_key)
        if "error" in result:
            st.session_state.messages.append({"role": "ai", "content": f"Error: {result['error']}"})
        else:
            try:
                content = result["choices"][0]["message"]["content"]
            except Exception:
                content = str(result)
            st.session_state.messages.append({"role": "ai", "content": content})

        # clear input after processing
        st.session_state.input_text = ""

    # input row (widgets must be created after send_message is defined)
    cols = st.columns([0.08, 0.82, 0.1])
    with cols[1]:
        st.text_input("You:", key="input_text", placeholder="Type a message and press Send", label_visibility="collapsed")
    with cols[2]:
        st.button("Send", on_click=send_message, use_container_width=True)

    # optional small help text
    st.markdown("<div class='small'>Tip: Choose Profile in the sidebar. Turn off 'Auto-detect' to force profile.</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# Teach panel
with st.expander("Teach Alpha (add custom response)"):
    teach_type = st.selectbox("User type", options=["general","beginner","expert","student","professional","lover"], key="teach_type")
    teach_q = st.text_input("Question (exact match)", key="teach_q")
    teach_a = st.text_area("Answer", key="teach_a")
    if st.button("Save teaching"):
        if not teach_q or not teach_a:
            st.error("Question and answer required.")
        else:
            ql = teach_q.strip().lower()
            if ql not in st.session_state.custom_responses:
                st.session_state.custom_responses[ql] = {}
            st.session_state.custom_responses[ql][teach_type] = teach_a.strip()
            st.success("Saved.")

# Weather quick action
with st.expander("Weather"):
    city = st.text_input("City", key="city_input")
    if st.button("Open weather"):
        if city:
            weather_url = f"https://www.google.com/search?q=weather+{city.replace(' ', '+')}"
            webbrowser.open(weather_url)
            st.info(f"Opened weather for {city} in browser.")
        else:
            st.warning("Provide a city.")

# Footer: debug info toggle
if st.checkbox("Show debug info"):
    # Do NOT show the API key even masked in debug mode
    st.write("Profile:", st.session_state.user_profile)
    st.write("Stored custom responses count:", len(st.session_state.custom_responses))