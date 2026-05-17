"""
Aspire English Hub - AI Service
================================
OpenAI integration for Whisper (STT), GPT (conversation), and TTS.
"""

from config import settings
from openai import AsyncOpenAI
from fastapi import HTTPException, UploadFile
import logging
import json
from typing import Optional, List, Dict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

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
    """AI service for speech-to-text, conversation, and text-to-speech."""

    @staticmethod
    async def speech_to_text(audio_file: UploadFile) -> dict:
        """Convert speech to text using Whisper."""
        if not client:
            raise HTTPException(status_code=503, detail="AI service not configured")
        try:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=(audio_file.filename, await audio_file.read(), audio_file.content_type),
                response_format="verbose_json"
            )
            return {
                "text": transcript.text,
                "language": getattr(transcript, "language", "en"),
                "duration": getattr(transcript, "duration", 0),
                "words": getattr(transcript, "words", [])
            }
        except Exception as e:
            logger.error(f"STT error: {str(e)}")
            raise HTTPException(status_code=500, detail="Speech recognition failed")

    @staticmethod
    async def get_ai_response(messages: List[Dict], mode: str = "casual", topic: str = None) -> dict:
        """Get GPT response for conversation."""
        if not client:
            raise HTTPException(status_code=503, detail="AI service not configured")
        try:
            system_prompt = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["casual"])
            if topic and mode == "topic_based":
                system_prompt += f"\n\nCurrent topic: {topic}"

            chat_messages = [{"role": "system", "content": system_prompt}] + messages

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=chat_messages,
                max_tokens=200,
                temperature=0.8
            )

            reply = response.choices[0].message.content
            return {"reply": reply, "usage": {"tokens": response.usage.total_tokens if response.usage else 0}}
        except Exception as e:
            logger.error(f"GPT error: {str(e)}")
            raise HTTPException(status_code=500, detail="AI response failed")

    @staticmethod
    async def text_to_speech(text: str, voice: str = "alloy") -> bytes:
        """Convert text to speech using OpenAI TTS."""
        if not client:
            raise HTTPException(status_code=503, detail="AI service not configured")
        try:
            response = await client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="mp3"
            )
            return response.content
        except Exception as e:
            logger.error(f"TTS error: {str(e)}")
            raise HTTPException(status_code=500, detail="Speech synthesis failed")

    @staticmethod
    async def analyze_speech(text: str) -> dict:
        """Analyze speech for grammar, fluency, vocabulary, and provide feedback."""
        if not client:
            return {"error": "AI not configured"}
        try:
            analysis_prompt = f"""Analyze this English speech and return a JSON object with:
            - pronunciation_score (0-100)
            - grammar_score (0-100)
            - fluency_score (0-100)
            - vocabulary_score (0-100)
            - confidence_score (0-100)
            - overall_score (0-100)
            - filler_words (list of filler words found like "um", "uh", "like")
            - grammar_errors (list of {{error, correction, explanation}})
            - vocabulary_suggestions (list of advanced word alternatives)
            - improvement_tips (list of 3 specific tips)
            - words_per_minute (estimated)
            
            Speech text: "{text}"
            
            Return ONLY valid JSON, no markdown."""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=800,
                temperature=0.3
            )

            result = response.choices[0].message.content.strip()
            if result.startswith("```"):
                result = result.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(result)
        except json.JSONDecodeError:
            return {"overall_score": 70, "improvement_tips": ["Keep practicing!"]}
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    async def generate_topic() -> dict:
        """Generate a random conversation topic."""
        if not client:
            return {"topic": "Tell me about your favorite hobby", "category": "general"}
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": 
                    "Generate 1 interesting English conversation topic. Return JSON: {\"topic\": \"...\", \"category\": \"general|interview|debate|ielts\", \"prompts\": [\"question1\", \"question2\"]}. Return ONLY JSON."}],
                max_tokens=150, temperature=1.0
            )
            result = response.choices[0].message.content.strip()
            if result.startswith("```"):
                result = result.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(result)
        except Exception:
            return {"topic": "What are your goals for the future?", "category": "general", "prompts": []}

    @staticmethod
    async def detect_toxic_content(text: str) -> dict:
        """Check text for toxic or inappropriate content."""
        if not client:
            return {"is_toxic": False}
        try:
            response = await client.moderations.create(input=text)
            result = response.results[0]
            return {
                "is_toxic": result.flagged,
                "categories": {k: v for k, v in result.categories.__dict__.items() if v}
            }
        except Exception:
            return {"is_toxic": False}


ai_service = AIService()
