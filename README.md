# Voice-Based Matrimony Chatbot

A quick demo Streamlit app for a voice chatbot simulating marriage meeting conversations.

## Features
- Select persona: Groom or Bride
- Voice input (Speech-to-Text using OpenAI Whisper)
- Natural conversation with GPT-4
- Voice response (Text-to-Speech using OpenAI TTS)
- Extract user information into JSON

## Setup
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

3. Run the app:
   ```
   streamlit run app.py
   ```

## Requirements
- Python 3.8+
- OpenAI API key
- Internet connection for OpenAI services