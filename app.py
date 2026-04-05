import streamlit as st
import openai
from dotenv import load_dotenv
import os

from utils.prompts import GROOM_PROMPT, BRIDE_PROMPT
from utils.llm import generate_audio, transcribe_audio, get_chatbot_response, extract_user_information

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    st.error("Please set your OPENAI_API_KEY in the .env file.")
    st.stop()

# Main UI
st.set_page_config(page_title="Voice-Based Matrimony Chatbot", page_icon="💍", layout="centered")
st.title("💍 Voice-Based Matrimony Chatbot")

# Sidebar for controls
with st.sidebar:
    st.header("Settings")
    persona = st.selectbox("Select Persona", ["Groom", "Bride"])
    
    if st.button("Start / Reset Conversation", use_container_width=True):
        st.session_state.history = []
        st.session_state.persona = persona
        st.session_state.voice = "onyx" if persona == "Groom" else "nova"
        st.session_state.active_prompt = GROOM_PROMPT if persona == "Groom" else BRIDE_PROMPT
        
        # Generate intro
        with st.spinner("Generating introduction..."):
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
                st.error(f"Failed to start conversation: {e}")
        st.rerun()

    st.divider()
    if st.button("Extract User Information", use_container_width=True):
        if "history" in st.session_state and len(st.session_state.history) > 0:
            with st.spinner("Extracting..."):
                extracted_data = extract_user_information(st.session_state.history)
            st.json(extracted_data)
        else:
            st.warning("No conversation history to extract from.")

# Main Chat Interface
if "history" not in st.session_state:
    st.info("👈 Please start a conversation from the sidebar.")
else:
    # Display chat history
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "audio" in msg and msg["audio"] is not None:
                autoplay = msg.get("autoplay", False)
                st.audio(msg["audio"], format="audio/mp3", autoplay=autoplay)
                if autoplay:
                    msg["autoplay"] = False

    # Audio input at the bottom
    if "audio_key" not in st.session_state:
        st.session_state.audio_key = 0

    audio_input = st.audio_input("Speak your message", key=f"audio_{st.session_state.audio_key}")

    if audio_input is not None:
        with st.spinner("Transcribing..."):
            try:
                transcript = transcribe_audio(audio_input)
            except Exception as e:
                st.error(f"Error transcribing audio: {e}")
                transcript = None
        
        if transcript:
            # 1. Add user message to history
            st.session_state.history.append({
                "role": "user",
                "content": transcript
            })
            
            # Show the user message immediately
            with st.chat_message("user"):
                st.markdown(transcript)
            
            # 2. Get bot response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        # Build context
                        system_msg = [{"role": "system", "content": st.session_state.active_prompt}]
                        context = [{"role": m["role"], "content": m["content"]} for m in st.session_state.history]
                        messages = system_msg + context
                        
                        bot_response_text = get_chatbot_response(messages)
                        bot_audio = generate_audio(bot_response_text, st.session_state.voice)
                        
                        # Add bot message to history
                        st.session_state.history.append({
                            "role": "assistant",
                            "content": bot_response_text,
                            "audio": bot_audio,
                            "autoplay": True
                        })
                        
                    except Exception as e:
                        st.error(f"Error generating AI response: {e}")
            
            # Increment the audio key to reset the input widget
            st.session_state.audio_key += 1
            st.rerun()