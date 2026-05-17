"""
Aspire English Hub - AI Service (Gemini Edition)
=================================================
Google Gemini API integration for Multimodal Speech-to-Text (STT), Chat, 
Speech Analysis, Content Moderation, and free Google TTS (gTTS) for Speech Synthesis.
"""

from config import settings
import google.generativeai as genai
from gtts import gTTS
from fastapi import HTTPException, UploadFile
import logging
import json
import io
from typing import Optional, List, Dict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Configure Gemini API
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)
    logger.info("✅ Gemini API successfully configured")
else:
    logger.warning("⚠️ Gemini API Key is missing. AI features will not work.")

# System prompts for different AI modes
SYSTEM_PROMPTS = {
    "casual": """You are a friendly English conversation partner named Alex. 
    Keep the conversation natural and engaging. Ask follow-up questions.
    Gently correct grammar mistakes. Use simple, clear English.
    Keep responses under 3 sentences.""",
    
    "interview": """You are a professional HR interviewer named Alex.
    Conduct a mock job interview. Ask common interview questions one at a time.
    Provide brief feedback on answers. Be professional but encouraging.
    Keep responses concise.""",
    
    "ielts": """You are an IELTS speaking test examiner named Alex.
    Follow the IELTS speaking test format with Parts 1, 2, and 3.
    Ask appropriate questions for each part. Evaluate based on IELTS criteria:
    fluency, vocabulary, grammar, and pronunciation. Keep responses brief.""",
    
    "debate": """You are a debate partner named Alex.
    Take the opposite position on topics. Present logical arguments.
    Challenge the student's points respectfully. Encourage critical thinking.
    Keep responses under 3 sentences.""",
    
    "topic_based": """You are an English conversation partner named Alex.
    Discuss the given topic in depth. Ask thought-provoking questions.
    Help expand vocabulary related to the topic. Keep responses natural and brief."""
}


class AIService:
    """AI service powered by Google Gemini and gTTS."""

    @staticmethod
    async def speech_to_text(audio_file: UploadFile) -> dict:
        """Convert speech to text using Gemini's native audio understanding."""
        if not settings.gemini_api_key:
            raise HTTPException(status_code=503, detail="Gemini AI service not configured")
        try:
            audio_bytes = await audio_file.read()
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            contents = [
                {
                    "mime_type": audio_file.content_type or "audio/webm",
                    "data": audio_bytes
                },
                "Transcribe this English audio speech accurately. Return ONLY the transcription text. Do not add any greetings, preamble, explanation, or notes. If the audio is silent or completely unintelligible, return an empty string."
            ]
            
            # Using async generation
            response = await model.generate_content_async(contents)
            text = response.text.strip() if response.text else ""
            
            return {
                "text": text,
                "language": "en",
                "duration": 0,
                "words": []
            }
        except Exception as e:
            logger.error(f"Gemini STT error: {str(e)}")
            raise HTTPException(status_code=500, detail="Speech recognition failed")

    @staticmethod
    async def get_ai_response(messages: List[Dict], mode: str = "casual", topic: str = None) -> dict:
        """Get Gemini response for conversation."""
        if not settings.gemini_api_key:
            raise HTTPException(status_code=503, detail="Gemini AI service not configured")
        try:
            system_prompt = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["casual"])
            if topic and mode == "topic_based":
                system_prompt += f"\n\nCurrent topic: {topic}"

            # Format the conversation history for Gemini (roles: 'user' or 'model')
            formatted_history = []
            for m in messages[:-1]:
                role = 'user' if m['role'] == 'user' else 'model'
                formatted_history.append({'role': role, 'parts': [m['content']]})

            # Create Gemini chat session with system instruction
            model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                system_instruction=system_prompt
            )
            chat = model.start_chat(history=formatted_history)

            # Send the latest user message
            last_msg = messages[-1]['content']
            response = await chat.send_message_async(last_msg)
            
            return {"reply": response.text.strip(), "usage": {"tokens": 0}}
        except Exception as e:
            logger.error(f"Gemini Chat error: {str(e)}")
            raise HTTPException(status_code=500, detail="AI response failed")

    @staticmethod
    async def text_to_speech(text: str, voice: str = "alloy") -> bytes:
        """Convert text to speech using completely free Google TTS (gTTS)."""
        try:
            # Generate high-quality speech synthesis from Google's TTS engine
            tts = gTTS(text=text, lang='en', slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except Exception as e:
            logger.error(f"gTTS Speech synthesis error: {str(e)}")
            raise HTTPException(status_code=500, detail="Speech synthesis failed")

    @staticmethod
    async def analyze_speech(text: str) -> dict:
        """Analyze speech for grammar, fluency, vocabulary, and provide feedback using Gemini's JSON Mode."""
        if not settings.gemini_api_key:
            return {"error": "Gemini AI not configured"}
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""Analyze this English speech and return a JSON object with:
            - pronunciation_score (integer between 0 and 100)
            - grammar_score (integer between 0 and 100)
            - fluency_score (integer between 0 and 100)
            - vocabulary_score (integer between 0 and 100)
            - confidence_score (integer between 0 and 100)
            - overall_score (integer between 0 and 100)
            - filler_words (list of strings representing filler words found, e.g., "um", "uh", "like")
            - grammar_errors (list of objects with keys: error, correction, explanation)
            - vocabulary_suggestions (list of strings containing advanced word alternatives)
            - improvement_tips (list of 3 specific tips as strings)
            - words_per_minute (integer estimating the speaking rate)
            
            Speech text: "{text}"
            """

            response = await model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {"overall_score": 70, "improvement_tips": ["Keep practicing!"]}
        except Exception as e:
            logger.error(f"Gemini Analysis error: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    async def generate_topic() -> dict:
        """Generate a random conversation topic."""
        if not settings.gemini_api_key:
            return {"topic": "Tell me about your favorite hobby", "category": "general"}
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = "Generate 1 interesting English conversation topic. Return a JSON object with keys: topic (string), category (string: 'general', 'interview', 'debate', or 'ielts'), prompts (list of strings for follow-up questions)."
            
            response = await model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            return json.loads(response.text)
        except Exception:
            return {"topic": "What are your goals for the future?", "category": "general", "prompts": []}

    @staticmethod
    async def detect_toxic_content(text: str) -> dict:
        """Check text for toxic or inappropriate content using Gemini's structured response."""
        if not settings.gemini_api_key:
            return {"is_toxic": False}
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""Analyze this text and check if it contains toxic, highly offensive, hateful, self-harm, sexual, or extremely inappropriate content.
            Return a JSON object with keys:
            - is_toxic (boolean)
            - categories (object containing boolean fields indicating flag categories if any)
            
            Text to analyze: "{text}"
            """
            
            response = await model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            return json.loads(response.text)
        except Exception:
            return {"is_toxic": False}


ai_service = AIService()
