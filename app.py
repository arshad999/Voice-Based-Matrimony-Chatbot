import streamlit as st
import openai
from dotenv import load_dotenv
import os
import base64

from utils.prompts import GROOM_PROMPT, BRIDE_PROMPT
from utils.llm import generate_audio, transcribe_audio, get_chatbot_response, get_chatbot_response_stream, extract_user_information

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    st.error("Please set your OPENAI_API_KEY in the .env file.")
    st.stop()

# Main UI Configuration
st.set_page_config(page_title="Voice-Based Matrimony Chatbot", page_icon="📞", layout="centered")

# Custom CSS for Phone Call UI
st.markdown("""
<style>
.phone-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 40vh;
    background: linear-gradient(135deg, #1e1e1e, #121212);
    border-radius: 30px;
    padding: 30px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.5);
    margin-top: 20px;
    margin-bottom: 20px;
    border: 1px solid #333;
}
.avatar {
    font-size: 80px;
    background: #2a2a2a;
    border-radius: 50%;
    width: 140px;
    height: 140px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 20px rgba(76, 175, 80, 0.4);
    animation: pulse 2s infinite;
    margin-bottom: 15px;
}
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.6); }
    70% { box-shadow: 0 0 0 25px rgba(76, 175, 80, 0); }
    100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
}
.status {
    color: #4CAF50;
    font-weight: 600;
    font-size: 1.1rem;
    margin-bottom: 10px;
    letter-spacing: 1px;
}
.subtitle-container {
    text-align: center;
    min-height: 80px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 20px;
}
.subtitle-bot {
    color: #ffffff;
    font-size: 1.4rem;
    font-weight: 500;
}
.subtitle-user {
    color: #888888;
    font-size: 1rem;
    font-style: italic;
}
</style>
""", unsafe_allow_html=True)

# Sidebar for controls
with st.sidebar:
    st.header("Call Settings")
    persona = st.selectbox("Select Contact", ["Groom", "Bride"])
    
    if st.button("Start / Reset Call", use_container_width=True):
        st.session_state.history = []
        st.session_state.persona = persona
        st.session_state.voice = "onyx" if persona == "Groom" else "nova"
        st.session_state.active_prompt = GROOM_PROMPT if persona == "Groom" else BRIDE_PROMPT
        
        # Generate intro
        with st.spinner("Connecting..."):
            intro_messages = [{"role": "system", "content": st.session_state.active_prompt + "\nIntroduce yourself naturally as if starting a marriage meeting conversation. Keep it short and friendly."}]
            try:
                intro_text = get_chatbot_response(intro_messages)
                intro_audio = generate_audio(intro_text, st.session_state.voice)
                
                st.session_state.history.append({
                    "role": "assistant",
                    "content": intro_text,
                    "audio": intro_audio,
                    "autoplay": True
                })
            except Exception as e:
                st.error(f"Call failed: {e}")
        st.rerun()

    st.divider()
    if st.button("Extract Partner Info", use_container_width=True):
        if "history" in st.session_state and len(st.session_state.history) > 0:
            with st.spinner("Extracting..."):
                extracted_data = extract_user_information(st.session_state.history)
            st.json(extracted_data)
        else:
            st.warning("No conversation history to extract from.")

# Main Call Interface
if "history" not in st.session_state:
    st.markdown("<h2 style='text-align: center; color: #555;'><br><br>👈 Please Start Call from the sidebar.</h2>", unsafe_allow_html=True)
else:
    # 1. Render the Phone Call screen
    persona_emoji = "👨" if st.session_state.persona == "Groom" else "👩"
    
    st.markdown(f"""
    <div class="phone-container">
        <div style="color: #888; font-size: 0.9rem; margin-bottom: 20px; font-weight: bold;">SECURE CALL</div>
        <div class="avatar">{persona_emoji}</div>
        <div class="status">Connected • Active</div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Process most recent subtitles
    recent_bot = ""
    recent_user = ""
    
    for msg in reversed(st.session_state.history):
        if msg["role"] == "assistant" and not recent_bot:
            recent_bot = msg["content"]
        elif msg["role"] == "user" and not recent_user:
            recent_user = msg["content"]
            
        if recent_bot and recent_user:
            break
            
    # Default subtitles layout frame
    subtitle_placeholder = st.empty()
    subtitle_placeholder.markdown(f"""
    <div class="subtitle-container">
        <div class="subtitle-bot">"{recent_bot}"</div>
        <div class="subtitle-user">You: {recent_user if recent_user else '[Listening...]'}</div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Audio Injection (Hidden)
    for msg in st.session_state.history:
        if "audio" in msg and msg.get("autoplay", False):
            b64_audio = base64.b64encode(msg["audio"]).decode()
            st.markdown(f'<audio autoplay src="data:audio/mp3;base64,{b64_audio}"></audio>', unsafe_allow_html=True)
            msg["autoplay"] = False

    # 4. Audio Input
    if "audio_key" not in st.session_state:
        st.session_state.audio_key = 0

    st.markdown("<br>", unsafe_allow_html=True)
    audio_input = st.audio_input("Speak", key=f"audio_{st.session_state.audio_key}")

    if audio_input is not None:
        with st.spinner("Transcribing..."):
            try:
                transcript = transcribe_audio(audio_input)
            except Exception as e:
                st.error(f"Error transcribing audio: {e}")
                transcript = None
        
        if transcript:
            st.session_state.history.append({"role": "user", "content": transcript})
            
            try:
                system_msg = [{"role": "system", "content": st.session_state.active_prompt}]
                context = [{"role": m["role"], "content": m["content"]} for m in st.session_state.history]
                messages = system_msg + context
                
                # Setup streaming visually into subtitles
                stream = get_chatbot_response_stream(messages)
                bot_response_text = ""
                
                for chunk in stream:
                    # Depending on streaming object syntax
                    content = chunk.choices[0].delta.content
                    if content:
                        bot_response_text += content
                        subtitle_placeholder.markdown(f"""
                        <div class="subtitle-container">
                            <div class="subtitle-bot" style="color: #4CAF50;">"{bot_response_text}"</div>
                            <div class="subtitle-user">You: {transcript}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                with st.spinner("Synthesizing Voice..."):
                    bot_audio = generate_audio(bot_response_text, st.session_state.voice)
                
                st.session_state.history.append({
                    "role": "assistant",
                    "content": bot_response_text,
                    "audio": bot_audio,
                    "autoplay": True
                })
                
            except Exception as e:
                st.error(f"Error generating AI response: {e}")
            
            st.session_state.audio_key += 1
            st.rerun()