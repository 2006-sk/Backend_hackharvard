from openai import OpenAI
import base64
import io
import wave
import os
from typing import Optional

# OpenAI client will be initialized when needed

def transcribe_audio_chunk(pcm16_bytes: bytes, sample_rate: int = 8000) -> Optional[str]:
    """
    Transcribe PCM16 audio using OpenAI Whisper API
    
    Args:
        pcm16_bytes: Raw PCM16 audio data
        sample_rate: Sample rate of the audio (default 8000 for Twilio)
    
    Returns:
        Transcribed text or None if transcription fails
    """
    try:
        # Initialize client when needed
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            print("❌ OpenAI API key not set. Please set OPENAI_API_KEY in .env file")
            return None
        
        client = OpenAI(api_key=api_key)
        
        # Convert PCM16 to WAV format for Whisper
        wav_buffer = io.BytesIO()
        
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit = 2 bytes
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm16_bytes)
        
        wav_buffer.seek(0)
        
        # Create a proper file-like object for OpenAI
        wav_buffer.name = "audio.wav"
        
        # Transcribe using OpenAI Whisper
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=wav_buffer,
            language="en"  # English
        )
        
        return response.text.strip()
        
    except Exception as e:
        print(f"Whisper transcription error: {e}")
        return None

def transcribe_audio_file(file_path: str) -> Optional[str]:
    """
    Transcribe audio file using OpenAI Whisper API
    
    Args:
        file_path: Path to audio file
    
    Returns:
        Transcribed text or None if transcription fails
    """
    try:
        # Initialize client when needed
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            print("❌ OpenAI API key not set. Please set OPENAI_API_KEY in .env file")
            return None
        
        client = OpenAI(api_key=api_key)
        
        with open(file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
        
        return response.text.strip()
        
    except Exception as e:
        print(f"Whisper file transcription error: {e}")
        return None
