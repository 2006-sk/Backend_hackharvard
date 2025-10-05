#!/usr/bin/env python3
"""
Test script to simulate audio forwarding from WebSocket to /transcribe/
"""

import asyncio
import websockets
import json
import base64
import wave
import math

def create_test_audio():
    """Create a simple test audio file and return as base64"""
    # Create a simple sine wave audio
    sample_rate = 8000
    duration = 1  # 1 second
    frequency = 440  # A note
    
    # Generate PCM audio data
    audio_data = []
    for i in range(int(sample_rate * duration)):
        sample = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
        audio_data.append(sample.to_bytes(2, byteorder='little', signed=True))
    
    # Convert to WAV format
    wav_data = b''
    # WAV header (simplified)
    wav_data += b'RIFF'
    wav_data += (36 + len(audio_data) * 2).to_bytes(4, 'little')
    wav_data += b'WAVE'
    wav_data += b'fmt '
    wav_data += (16).to_bytes(4, 'little')  # fmt chunk size
    wav_data += (1).to_bytes(2, 'little')   # PCM format
    wav_data += (1).to_bytes(2, 'little')   # mono
    wav_data += sample_rate.to_bytes(4, 'little')
    wav_data += (sample_rate * 2).to_bytes(4, 'little')  # byte rate
    wav_data += (2).to_bytes(2, 'little')   # block align
    wav_data += (16).to_bytes(2, 'little')  # bits per sample
    wav_data += b'data'
    wav_data += (len(audio_data) * 2).to_bytes(4, 'little')
    wav_data += b''.join(audio_data)
    
    # Convert to base64
    return base64.b64encode(wav_data).decode('utf-8')

async def test_audio_forwarding():
    """Test WebSocket audio forwarding"""
    uri = "ws://localhost:8000/media"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔌 Connected to WebSocket")
            
            # Send start event
            await websocket.send(json.dumps({
                "event": "start",
                "start": {"streamSid": "MZ1234567890abcdef"}
            }))
            print("📤 Sent start event")
            
            # Create test audio and send as media frames
            test_audio_b64 = create_test_audio()
            print(f"🎵 Created test audio (base64 length: {len(test_audio_b64)})")
            
            # Send multiple media frames
            for i in range(3):
                await websocket.send(json.dumps({
                    "event": "media",
                    "media": {
                        "payload": test_audio_b64,
                        "timestamp": str(i * 1000)
                    }
                }))
                print(f"📤 Sent media frame {i+1}")
                await asyncio.sleep(0.5)  # Wait between frames
            
            # Send stop event
            await websocket.send(json.dumps({"event": "stop"}))
            print("📤 Sent stop event")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing audio forwarding...")
    print("Make sure your FastAPI server is running on localhost:8000")
    asyncio.run(test_audio_forwarding())
