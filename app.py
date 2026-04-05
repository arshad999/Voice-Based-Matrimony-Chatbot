import streamlit as st
import openai
from dotenv import load_dotenv
import os
import json

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    st.error("Please set your OPENAI_API_KEY in the .env file.")
    st.stop()

# Define personas
groom_prompt = """
You are a groom in a casual marriage meeting conversation. Be warm, friendly, and a little shy.
Talk naturally in a mix of English and Indian conversational tone (Hinglish style).
Let the conversation flow naturally like two people getting to know each other for the first time.
Share bits about yourself, respond genuinely to what the other person says, and show real interest in them.

IMPORTANT GUIDELINES:
- Make responses realistic and natural - sometimes share more, sometimes less. Vary your response length based on the context.
- Don't keep responses too short. Share genuine thoughts and experiences that feel real and relatable.
- Show some nervousness or hesitation sometimes - it's natural in these situations. Maybe say "uhh" or "well" or take a moment to think.
- Ask at most ONE question per response, and only when it feels natural.
- Early in the conversation, naturally ask for their name in a casual way.
- Respond to what they say genuinely - don't just wait to ask the next question. Have a real conversation.
- Share anecdotes, reactions, and opinions that make you seem like a real person with feelings and experiences.
- Don't go too deep into side topics (like movies, hobbies, etc.). After briefly acknowledging their interest, smoothly divert the conversation towards extracting key information (age, location, profession, education, family background, career interests, preferences).
- Use transitions like "That's cool, by the way..." or "Oh nice, so..." to smoothly move away from tangential topics towards learning more about them.
- Smoothly extract personal information through natural conversation over multiple exchanges, but don't get stuck on any single topic.
- Sometimes acknowledge what they said before moving forward - create continuity in the chat.
"""

bride_prompt = """
You are a bride in a casual marriage meeting conversation. Be warm, friendly, and a little shy.
Talk naturally in a mix of English and Indian conversational tone (Hinglish style).
Let the conversation flow naturally like two people getting to know each other for the first time.
Share bits about yourself, respond genuinely to what the other person says, and show real interest in them.

IMPORTANT GUIDELINES:
- Make responses realistic and natural - sometimes share more, sometimes less. Vary your response length based on the context.
- Don't keep responses too short. Share genuine thoughts and experiences that feel real and relatable.
- Show some nervousness or hesitation sometimes - it's natural in these situations. Maybe say "uhh" or "well" or take a moment to think.
- Ask at most ONE question per response, and only when it feels natural.
- Early in the conversation, naturally ask for their name in a casual way.
- Respond to what they say genuinely - don't just wait to ask the next question. Have a real conversation.
- Share anecdotes, reactions, and opinions that make you seem like a real person with feelings and experiences.
- Don't go too deep into side topics (like movies, hobbies, etc.). After briefly acknowledging their interest, smoothly divert the conversation towards extracting key information (age, location, profession, education, family background, career interests, preferences).
- Use transitions like "That's cool, by the way..." or "Oh nice, so..." to smoothly move away from tangential topics towards learning more about them.
- Smoothly extract personal information through natural conversation over multiple exchanges, but don't get stuck on any single topic.
- Sometimes acknowledge what they said before moving forward - create continuity in the chat.
"""

# Helper Functions
def generate_audio(text: str, voice: str) -> bytes:
    """Generate audio bytes using OpenAI TTS."""
    response = openai.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    return response.content

def transcribe_audio(audio_file) -> str:
    """Transcribe user audio to text using Whisper."""
    response = openai.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return response.text

def get_chatbot_response(messages: list) -> str:
    """Get the next chat response from GPT-4o."""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    return response.choices[0].message.content

def extract_user_information(history: list) -> dict:
    """Extract information from the chat history and return as a JSON dictionary."""
    extract_prompt = """
    From the conversation, extract the following user information if mentioned:
    - name
    - age
    - location
    - profession
    - salary
    - education
    - family_details
    - hobbies
    - preferences (partner expectations)
    
    Output as ONLY a valid JSON object. If a field is not mentioned, use null for it.
    Ensure all extracted information is in English; translate any Hinglish or non-English text to English.
    """
    # format history for context
    context = [{"role": m["role"], "content": m["content"]} for m in history]
    
    messages = [{"role": "system", "content": extract_prompt}] + context
    
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON", "raw": content}

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
        st.session_state.active_prompt = groom_prompt if persona == "Groom" else bride_prompt
        
        # Generate intro
        with st.spinner("Generating introduction..."):
            intro_messages = [{"role": "system", "content": st.session_state.active_prompt + "\nIntroduce yourself naturally as if starting a marriage meeting conversation. Keep it short and friendly."}]
            try:
                intro_text = get_chatbot_response(intro_messages)
                intro_audio = generate_audio(intro_text, st.session_state.voice)
                
                st.session_state.history.append({
                    "role": "assistant",
                    "content": intro_text,
                    "audio": intro_audio
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
                st.audio(msg["audio"], format="audio/mp3")

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
                            "audio": bot_audio
                        })
                        
                        st.markdown(bot_response_text)
                        st.audio(bot_audio, format="audio/mp3")
                        
                    except Exception as e:
                        st.error(f"Error generating AI response: {e}")
            
            # Increment the audio key to reset the input widget
            st.session_state.audio_key += 1
            st.rerun()