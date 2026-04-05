import openai
import json
from .prompts import EXTRACT_PROMPT

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
    """Get the next chat response from GPT-4o-mini."""
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    return response.choices[0].message.content

def get_chatbot_response_stream(messages: list):
    """Get the next chat response from GPT-4o-mini as a stream."""
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True
    )
    return response

def extract_user_information(history: list) -> dict:
    """Extract information from the chat history and return as a JSON dictionary."""
    # format history for context
    context = [{"role": m["role"], "content": m["content"]} for m in history]
    
    messages = [{"role": "system", "content": EXTRACT_PROMPT}] + context
    
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
