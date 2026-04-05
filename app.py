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

st.title("Voice-Based Matrimony Chatbot")

# Select persona
persona = st.selectbox("Select Persona", ["Groom", "Bride"])
st.session_state.persona = persona

if st.button("Start Conversation"):
    st.session_state.history = []
    st.session_state.user_data = {}

    # Generate introduction
    prompt = groom_prompt if st.session_state.persona == "Groom" else bride_prompt
    intro_messages = [{"role": "system", "content": prompt + "\nIntroduce yourself naturally as if starting a marriage meeting conversation. Keep it short and friendly."}]
    intro_response = openai.chat.completions.create(
        model="gpt-4o",
        messages=intro_messages
    ).choices[0].message.content

    st.session_state.history.append({"role": "assistant", "content": intro_response})

    # TTS for intro
    try:
        voice = "onyx" if st.session_state.persona == "Groom" else "nova"
        tts_response = openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=intro_response
        )
        audio_bytes = b""
        for chunk in tts_response.iter_bytes():
            audio_bytes += chunk

        st.audio(audio_bytes, format="audio/mp3")
    except Exception as e:
        st.error(f"Error generating voice for introduction: {e}")
    # st.write(f"Bot: {intro_response}")  # Removed text display for voice focus

# Display chat history
if "history" in st.session_state:
    st.subheader("Conversation")
    for msg in st.session_state.history:
        if msg["role"] == "user":
            st.write(f"**You:** {msg['content']}")
        else:
            st.write(f"**Bot:** {msg['content']}")

# Audio input
audio_input = st.audio_input("Speak your message")

if audio_input is not None:
    # Transcribe audio
    try:
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_input
        ).text
        st.write(f"You said: {transcript}")
    except Exception as e:
        st.error(f"Error transcribing audio: {e}")
        transcript = ""  # or continue

    if transcript:
        # Add to history
        if "history" not in st.session_state:
            st.session_state.history = []
        st.session_state.history.append({"role": "user", "content": transcript})

        # Get bot response
        try:
            prompt = groom_prompt if st.session_state.persona == "Groom" else bride_prompt
            messages = [{"role": "system", "content": prompt}] + st.session_state.history
            response = openai.chat.completions.create(
                model="gpt-4o",  # Use latest GPT model
                messages=messages
            ).choices[0].message.content

            st.session_state.history.append({"role": "assistant", "content": response})

            # Text-to-Speech
            try:
                voice = "onyx" if st.session_state.persona == "Groom" else "nova"
                tts_response = openai.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=response
                )
                audio_bytes = b""
                for chunk in tts_response.iter_bytes():
                    audio_bytes += chunk

                st.audio(audio_bytes, format="audio/mp3")
            except Exception as e:
                st.error(f"Error generating voice response: {e}")
        except Exception as e:
            st.error(f"Error generating bot response: {e}")
    # st.write(f"Bot: {response}")  # Removed text display for voice focus

# Extract data
if st.button("Extract User Information"):
    if "history" in st.session_state and st.session_state.history:
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
        Output as a valid JSON object. If not mentioned, use null.
        Ensure all extracted information is in English; translate any Hinglish or non-English text to English.
        """
        messages = [{"role": "system", "content": extract_prompt}] + st.session_state.history
        extract_response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages
        ).choices[0].message.content
        try:
            data = json.loads(extract_response)
            st.json(data)
        except:
            st.write("Failed to parse JSON. Raw response:")
            st.write(extract_response)
    else:
        st.write("No conversation history to extract from.")