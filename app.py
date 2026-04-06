import streamlit as st
import openai
from dotenv import load_dotenv
import os
import base64
import time
import uuid
import streamlit.components.v1 as components

from utils.prompts import GROOM_PROMPT, BRIDE_PROMPT
from utils.llm import generate_audio, get_chatbot_response, get_chatbot_response_stream, extract_user_information

# Declare the lightweight, continuous speech custom React/HTML component
continuous_speech = components.declare_component("continuous_speech", path="components/continuous_speech")

# ----------------- App Initialization ----------------- #
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    st.error("Please set your OPENAI_API_KEY in the .env file.")
    st.stop()

st.set_page_config(page_title="Voice Matrimony Bot", page_icon="📞", layout="centered")

# ----------------- Custom CSS (Glassmorphism & UX) ----------------- #
st.markdown("""
<style>
/* Base Theme Tweaks */
.stApp {
    background-color: #0e0e0e;
}

/* Glassmorphic Phone Container */
.phone-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 45vh;
    background: rgba(25, 25, 25, 0.65);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-radius: 40px;
    padding: 40px 20px;
    box-shadow: 0 30px 60px rgba(0, 0, 0, 0.4), inset 0 0 0 1px rgba(255, 255, 255, 0.08);
    margin: 20px auto 30px auto;
    max-width: 380px;
    position: relative;
}

/* Pulsating Avatar */
.avatar {
    font-size: 85px;
    background: linear-gradient(145deg, #222, #111);
    border-radius: 50%;
    width: 150px;
    height: 150px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 25px rgba(0, 230, 118, 0.3), inset 0 0 15px rgba(255, 255, 255, 0.05);
    animation: pulse 2.5s infinite cubic-bezier(0.66, 0, 0, 1);
    margin-bottom: 25px;
    border: 2px solid rgba(0, 230, 118, 0.2);
    user-select: none;
}
@keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(0, 230, 118, 0.5); }
    100% { box-shadow: 0 0 0 45px rgba(0, 230, 118, 0); }
}

/* Secure Call Label */
.secure-call-label {
    color: #b0bec5;
    font-size: 0.8rem;
    margin-bottom: 25px;
    font-weight: 600;
    letter-spacing: 2.5px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.secure-icon {
    color: #00e676;
}

/* Subtitles Styling */
.subtitle-container {
    text-align: center;
    min-height: 90px;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    gap: 12px;
    margin-bottom: 25px;
    padding: 0 20px;
}
.subtitle-bot {
    color: #ffffff;
    font-size: 1.35rem;
    font-weight: 500;
    line-height: 1.4;
    text-shadow: 0 2px 4px rgba(0,0,0,0.5);
}
.subtitle-bot.active {
    color: #00e676;
}
.subtitle-user {
    color: #9e9e9e;
    font-size: 1.05rem;
    font-style: italic;
    font-weight: 400;
}

/* End Call Button Override */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #d32f2f, #b71c1c);
    color: white;
    border: none;
    border-radius: 30px;
    font-weight: 600;
    padding: 12px 24px;
    box-shadow: 0 8px 16px rgba(211, 47, 47, 0.3);
    transition: all 0.2s ease;
}
div.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #f44336, #d32f2f);
    box-shadow: 0 10px 20px rgba(211, 47, 47, 0.4);
    transform: translateY(-2px);
}
</style>
""", unsafe_allow_html=True)

# ----------------- Helper Functions ----------------- #
def render_subtitles(bot_text: str, user_text: str, is_active: bool = False):
    """Renders the dynamic subtitle UI cleanly."""
    active_class = " active" if is_active else ""
    return f"""
    <div class="subtitle-container">
        <div class="subtitle-bot{active_class}">"{bot_text}"</div>
        <div class="subtitle-user">You: {user_text if user_text else '[Listening...]'}</div>
    </div>
    """

def end_active_call():
    """Clear session states related to active call."""
    for key in ["history", "call_start_time", "last_transcript_id"]:
        if key in st.session_state:
            del st.session_state[key]

# ----------------- Sidebar Controls ----------------- #
with st.sidebar:
    st.header("⚙️ Settings")
    persona = st.selectbox("Select Partner Persona", ["Groom", "Bride"])
    
    if st.button("🚀 Start / Reset Call", use_container_width=True):
        end_active_call() # Clean up before starting new
        st.session_state.history = []
        st.session_state.persona = persona
        st.session_state.call_start_time = time.time()
        
        st.session_state.voice = "onyx" if persona == "Groom" else "nova"
        st.session_state.active_prompt = GROOM_PROMPT if persona == "Groom" else BRIDE_PROMPT
        
        with st.spinner("Connecting securely..."):
            intro_messages = [{"role": "system", "content": st.session_state.active_prompt + "\nIntroduce yourself naturally. Keep it extremely short and friendly."}]
            try:
                intro_text = get_chatbot_response(intro_messages)
                intro_audio = generate_audio(intro_text, st.session_state.voice)
                
                st.session_state.history.append({
                    "role": "assistant",
                    "content": intro_text,
                    "audio": intro_audio,
                    "autoplay": True
                })
                st.session_state.bot_speak_id = str(uuid.uuid4())
                st.session_state.bot_word_count = len(intro_text.split())
            except Exception as e:
                st.error(f"Call connection failed: {e}")
        st.rerun()

    st.divider()
    if st.button("📊 Extract Partner Profile", use_container_width=True):
        if "history" in st.session_state and len(st.session_state.history) > 0:
            with st.spinner("Analyzing conversation..."):
                extracted_data = extract_user_information(st.session_state.history)
            st.success("Extraction Complete")
            st.json(extracted_data)
        else:
            st.warning("No conversation history available.")

# ----------------- Main Interface ----------------- #
if "history" not in st.session_state:
    st.markdown("""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:60vh; color:#666;">
            <h1 style="font-size:4rem; margin-bottom:10px;">📞</h1>
            <h2>Ready to Connect</h2>
            <p>Please Start the Call from the sidebar settings.</p>
        </div>
    """, unsafe_allow_html=True)
else:
    # --- 1. Phone Call UI ---
    persona_emoji = "👨" if st.session_state.persona == "Groom" else "👩"
    start_t = st.session_state.get("call_start_time", time.time())
    
    # Custom interactive timer iframe
    iframe_srcdoc = f"""
    <html>
    <head>
        <style>
            body {{
                margin: 0; padding: 0; text-align: center;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-weight: 500; font-size: 1.05rem; letter-spacing: 1.5px;
                color: #00e676; overflow: hidden; background: transparent;
            }}
        </style>
    </head>
    <body>
        <div id='timer'>00:00</div>
        <script>
            var start = {start_t};
            function update() {{
                var e = Math.floor(Date.now() / 1000 - start);
                var m = Math.floor(e / 60).toString().padStart(2, '0');
                var s = (e % 60).toString().padStart(2, '0');
                document.getElementById('timer').innerHTML = m + ':' + s;
            }}
            setInterval(update, 1000);
            update();
        </script>
    </body>
    </html>
    """.replace('"', '&quot;')
    
    st.markdown(f"""
    <div class="phone-container">
        <div class="secure-call-label">
            <span class="secure-icon">🔒</span> END-TO-END ENCRYPTED
        </div>
        <div class="avatar">{persona_emoji}</div>
        <iframe srcdoc="{iframe_srcdoc}" style="border:none; width:100px; height:30px; background:transparent;" scrolling="no"></iframe>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.button("🚫 End Call", use_container_width=True, type="primary", on_click=end_active_call)

    # --- 2. Subtitles Parsing ---
    recent_bot, recent_user = "", ""
    for msg in reversed(st.session_state.history):
        if msg["role"] == "assistant" and not recent_bot:
            recent_bot = msg["content"]
        elif msg["role"] == "user" and not recent_user:
            recent_user = msg["content"]
        if recent_bot and recent_user:
            break
            
    subtitle_placeholder = st.empty()
    subtitle_placeholder.markdown(render_subtitles(recent_bot, recent_user), unsafe_allow_html=True)

    # --- 3. Audio Injection ---
    for msg in st.session_state.history:
        if "audio" in msg and msg.get("autoplay", False):
            b64_audio = base64.b64encode(msg["audio"]).decode()
            st.markdown(f'<audio autoplay src="data:audio/mp3;base64,{b64_audio}"></audio>', unsafe_allow_html=True)
            msg["autoplay"] = False

    # --- 4. Continuous Input & Processing ---
    speak_id = st.session_state.get("bot_speak_id", None)
    word_count = st.session_state.get("bot_word_count", 0)
    lang_code = st.session_state.get("lang_code", "en-IN")
    
    transcript_payload = continuous_speech(
        speak_id=speak_id, 
        word_count=word_count, 
        language=lang_code,
        key="continuous_voice"
    )

    transcript = None
    if transcript_payload:
        tid = transcript_payload.get("timestamp")
        if tid != st.session_state.get("last_transcript_id"):
            st.session_state["last_transcript_id"] = tid
            transcript = transcript_payload.get("text")

    if transcript:
        st.session_state.history.append({"role": "user", "content": transcript})
        
        try:
            # Prepare streaming UI
            subtitle_placeholder.markdown(render_subtitles("...", transcript, is_active=True), unsafe_allow_html=True)
            
            system_msg = [{"role": "system", "content": st.session_state.active_prompt}]
            context = [{"role": m["role"], "content": m["content"]} for m in st.session_state.history]
            messages = system_msg + context
            
            stream = get_chatbot_response_stream(messages)
            bot_response_text = ""
            
            # Real-time subtitle streaming
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    content = chunk.choices[0].delta.content
                    if content:
                        bot_response_text += content
                        subtitle_placeholder.markdown(render_subtitles(bot_response_text, transcript, is_active=True), unsafe_allow_html=True)
            
            # Audio Synthesis
            with st.spinner("Synthesizing Voice..."):
                bot_audio = generate_audio(bot_response_text, st.session_state.voice)
            
            st.session_state.history.append({
                "role": "assistant",
                "content": bot_response_text,
                "audio": bot_audio,
                "autoplay": True
            })
            
            st.session_state.bot_speak_id = str(uuid.uuid4())
            st.session_state.bot_word_count = len(bot_response_text.split())
            
        except Exception as e:
            st.error(f"Network error or processing failed: {str(e)}")
        
        st.rerun()