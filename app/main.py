from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import Response
import wave, json, base64
import os
import asyncio
import numpy as np
import threading
import httpx
from datetime import datetime
from app.utils_audio import decode_twilio_payload
from app.whisper_client import transcribe_audio_chunk, transcribe_audio_file
from pydantic import BaseModel
from app.detector.fuzzywords import scam_score, check_keywords
from app.detector.ml_model import predict_scam_probability
from app.detector.advanced_scam_detector import analyze_text_segment, get_call_risk_summary, cleanup_call_detection
from app.detector.ensemble_detector import get_ensemble_detector, analyze_with_ensemble
from app.detector.model_evaluator import evaluate_ensemble_model, ModelEvaluator
from app.detector.quick_evaluator import quick_evaluate, QuickEvaluator
from app.detector.improved_ensemble import get_improved_ensemble_detector, analyze_with_improved_ensemble
from app.preprocessor.fuzzy_transcript import merge_transcripts, should_break_segment
from app.media_bridge import bridge
import logging
from app.scam_model import get_model
from fastapi.middleware.cors import CORSMiddleware
from routes.r2_routes import router as r2_router
# R2 upload removed - no recording needed
from database import db

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import boto3 for Cloudflare R2 support
try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("⚠️ boto3 not available - Cloudflare R2 upload will be disabled")

# Global lock for file writing to prevent concurrent access
transcript_file_lock = threading.Lock()
TRANSCRIPT_FILE_PATH = "live_transcript.txt"

# Global dictionary to maintain transcripts per call session
active_calls = {}

# Global set to track connected frontend WebSocket clients
connected_frontends = set()

# Global variable for adaptive risk scoring
recent_risk_score = 0.0
DECAY_RATE = 0.115

# Global variable for test transcription
recent_transcripts = []

# Global variable for current active Twilio stream
current_stream_sid: str = None

# Frontend URL for posting stream updates
FRONTEND_URL = "http://localhost:5174/api/stream-start"  # Frontend at localhost:5174

# Real-time analysis only - no chunk storage needed

# R2 configuration removed - no recording needed

def get_risk_band(score):
    """Get risk band based on score"""
    if score < 0.4:
        return "LOW"
    elif score < 0.7:
        return "MEDIUM"
    else:
        return "HIGH"

async def broadcast_to_frontends(message: dict):
    """Broadcast a message to all connected frontend WebSocket clients"""
    if connected_frontends:
        disconnected = set()
        for websocket in connected_frontends:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"[WS] Failed to send to frontend: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            connected_frontends.discard(websocket)
        
        print(f"[WS] Broadcasted to {len(connected_frontends)} frontend clients")
    else:
        print("[WS] No frontend clients connected")

async def notify_frontend(event_data: dict):
    """Helper function to send notifications to all connected frontend clients"""
    await broadcast_to_frontends(event_data)

def upload_to_r2(file_path: str) -> str:
    """Upload a file to Cloudflare R2 and return the public URL"""
    if not BOTO3_AVAILABLE:
        raise Exception("boto3 not available - cannot upload to R2")
    
    if not all([R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, R2_ACCOUNT_ID]):
        raise Exception("Cloudflare R2 credentials not configured")
    
    # Create S3 client for Cloudflare R2
    s3_client = boto3.client(
        's3',
        endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name='auto'
    )
    
    # Extract filename from path
    filename = os.path.basename(file_path)
    
    try:
        # Upload file to R2
        s3_client.upload_file(file_path, R2_BUCKET_NAME, filename)
        
        # Return public URL (assuming public bucket)
        public_url = f"https://{R2_BUCKET_NAME}.{R2_ACCOUNT_ID}.r2.cloudflarestorage.com/{filename}"
        
        logger.info(f"Successfully uploaded {filename} to R2: {public_url}")
        return public_url
        
    except ClientError as e:
        logger.error(f"Failed to upload to R2: {e}")
        raise Exception(f"R2 upload failed: {str(e)}")

def write_transcript_to_file(text: str):
    """Write transcript text to live_transcript.txt file with thread safety and scam analysis"""
    transcript_text = text.strip()
    if not transcript_text:
        return
    
    with transcript_file_lock:
        try:
            # Write to live transcript file
            with open(TRANSCRIPT_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(transcript_text + "\n")
            logger.info(f"📝 Written to transcript file: {transcript_text}")
            
            # Analyze for scam indicators
            score = scam_score(transcript_text)
            matches = check_keywords(transcript_text)
            
            # Print scam analysis to terminal
            if score >= 50:
                print(f"⚠️ HIGH SCAM SCORE {score}% — {matches}")
            else:
                print(f"[SAFE] {transcript_text} ({score}%)")
            
            # Log to scam log file
            with open("scam_log.txt", "a", encoding="utf-8") as log:
                log.write(f"{score}% | {matches} | {transcript_text}\n")
                
        except Exception as e:
            logger.error(f"❌ Failed to write transcript to file: {e}")

def initialize_transcript_file():
    """Initialize/clear the transcript file for a new session"""
    with transcript_file_lock:
        try:
            with open(TRANSCRIPT_FILE_PATH, "w", encoding="utf-8") as f:
                f.write("")  # Clear the file
            logger.info("📄 Initialized live_transcript.txt for new session")
        except Exception as e:
            logger.error(f"❌ Failed to initialize transcript file: {e}")

def finalize_transcript_file():
    """Add call end marker to transcript file"""
    with transcript_file_lock:
        try:
            with open(TRANSCRIPT_FILE_PATH, "a", encoding="utf-8") as f:
                f.write("---- Call ended ----\n")
            logger.info("📄 Added call end marker to transcript file")
        except Exception as e:
            logger.error(f"❌ Failed to finalize transcript file: {e}")


# Optional noise reduction import
try:
    import noisereduce as nr
    NOISE_REDUCTION_AVAILABLE = True
    logger.info("✅ Noise reduction module loaded")
except ImportError:
    NOISE_REDUCTION_AVAILABLE = False
    logger.warning("⚠️  Noise reduction not available - install noisereduce for better audio quality")

def denoise_pcm(pcm16_bytes: bytes) -> bytes:
    """Reduce background noise in 8 kHz mono PCM16 audio."""
    if not NOISE_REDUCTION_AVAILABLE:
        return pcm16_bytes  # Return original audio if noise reduction not available
    
    try:
        data = np.frombuffer(pcm16_bytes, dtype=np.int16)
        reduced = nr.reduce_noise(y=data, sr=8000)
        return reduced.astype(np.int16).tobytes()
    except Exception as e:
        logger.warning(f"⚠️  Noise reduction failed, using original audio: {e}")
        return pcm16_bytes

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Check OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
    logger.warning("⚠️  OpenAI API key not set. Please update .env file with your OpenAI API key.")
    logger.warning("   Set OPENAI_API_KEY=your_actual_key_here in .env file")
    # Don't raise error, let it fail gracefully when trying to use Whisper
else:
    logger.info("✅ OpenAI API key loaded")

# Pydantic models
class TranscriptInput(BaseModel):
    transcript: str

class AudioPayload(BaseModel):
    payload: str

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include R2 routes
app.include_router(r2_router)

@app.on_event("startup")
async def check_r2_connection():
    """Check R2 connection on startup"""
    try:
        from routes.r2_routes import check_r2_connection
        result = await check_r2_connection()
        if result.get("status") == "ok":
            print("✅ R2 Connected")
            print(f"📦 Bucket: {result.get('bucket')}")
            print(f"📊 Total buckets: {result.get('total_buckets')}")
        else:
            print("❌ R2 Connection Failed")
            print(f"Error: {result.get('message')}")
    except Exception as e:
        print(f"❌ R2 Startup Check Failed: {e}")
@app.get("/")
def home():
    return {"msg": "ScamShield AI Backend Running with OpenAI Whisper!"}

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/voice")
def voice():
    """TwiML endpoint for Twilio voice calls"""
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Hello! This is ScamShield AI. I'm will be analyzing your call for potential scam indicators.</Say>
    <Start>
        <Stream url="wss://submammary-correlatively-irma.ngrok-free.dev/media" />
    </Start>
    <Pause length="60"/>
</Response>"""
    
    return Response(content=twiml, media_type="application/xml")

async def transcribe_with_whisper(audio_data: bytes, sample_rate: int = 8000):
    """Async wrapper for Whisper transcription to avoid blocking WebSocket"""
    def _transcribe():
        return transcribe_audio_chunk(audio_data, sample_rate)
    
    # Run transcription in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _transcribe)

async def process_audio_chunk(audio_data: bytes, sample_rate: int, stream_sid: str = None):
    """Process audio chunk with parallel transcription, analysis, DB, and frontend updates"""
    try:
        # Transcribe using OpenAI Whisper
        transcript = await transcribe_with_whisper(audio_data, sample_rate)
        
        if transcript and transcript.strip():
            logger.info(f"[RAW] {transcript}")
            print(f"[MAIN] Processing transcript: '{transcript}'")
            
            # Use improved ensemble detector with enhanced features
            if stream_sid:
                print(f"[MAIN] Calling improved ensemble detector for stream: {stream_sid}")
                analysis = analyze_with_improved_ensemble(transcript, stream_sid)
                print(f"[MAIN] Improved ensemble result: {analysis}")
                
                # Log the improved ensemble analysis
                logger.info(f"[ENSEMBLE] Text: '{transcript[:50]}...'")
                logger.info(f"[ENSEMBLE] Final Score: {analysis['ensemble_score']:.3f} ({analysis['risk_band']})")
                logger.info(f"[ENSEMBLE] Advanced: {analysis['advanced_score']:.3f}, ML: {analysis['ml_score']:.3f}")
                
                # Update global risk score with the ensemble score
                global recent_risk_score
                recent_risk_score = analysis['ensemble_score']
                logger.info(f"[RISK UPDATE] Global risk score updated to: {recent_risk_score:.3f}")
                
                # Run operations in parallel for real-time processing
                await asyncio.gather(
                    # File operations (non-blocking)
                    asyncio.create_task(_write_improved_analysis_file(analysis)),
                    asyncio.create_task(_write_transcript_file(transcript)),
                    
                    # Frontend notification (non-blocking)
                    asyncio.create_task(_notify_frontend_async(stream_sid, transcript, analysis)),
                    
                    return_exceptions=True  # Don't fail if one operation fails
                )
            else:
                # Fallback for cases without stream_sid
                logger.warning("No stream_sid provided for advanced detection")
                write_transcript_to_file(transcript)
        else:
            logger.debug("No transcript generated for audio chunk")
            
    except Exception as e:
        logger.error(f"❌ Audio chunk processing error: {e}")

# Parallel processing helper functions
async def _write_analysis_file(analysis):
    """Write analysis to file asynchronously"""
    try:
        with open("live_analysis.txt", "a") as f:
            ts = datetime.utcnow().isoformat()
            f.write(f"{ts} | {analysis['segment']} | risk={analysis['smoothed_risk']:.3f} | band={analysis['risk_band']} | matches={analysis['high_risk_matches']}\n")
    except Exception as e:
        logger.error(f"❌ Analysis file write error: {e}")

async def _write_transcript_file(segment):
    """Write transcript to file asynchronously"""
    try:
        write_transcript_to_file(segment)
    except Exception as e:
        logger.error(f"❌ Transcript file write error: {e}")

async def _write_improved_analysis_file(analysis: dict):
    """Write improved ensemble analysis results to file (async)"""
    try:
        with open("live_analysis.txt", "a") as f:
            ts = datetime.utcnow().isoformat()
            f.write(f"{ts} | ensemble={analysis['ensemble_score']:.3f} | advanced={analysis['advanced_score']:.3f} | ml={analysis['ml_score']:.3f} | band={analysis['risk_band']} | method={analysis['method']}\n")
    except Exception as e:
        logger.error(f"❌ Improved analysis file write error: {e}")

# Removed _store_transcript_async - now storing complete transcript only at call end

async def _push_to_r2_async(stream_sid: str, complete_transcript: str, risk_score: float, risk_band: str, duration: float):
    """Push complete transcript and risk data to R2 storage"""
    try:
        import httpx
        
        # Prepare transcript data for R2
        transcript_data = {
            "chunk_id": "complete_transcript",
            "data": complete_transcript,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "call_duration": duration,
                "stream_sid": stream_sid,
                "source": "live_transcript.txt"
            }
        }
        
        # Upload transcript to R2
        async with httpx.AsyncClient() as client:
            transcript_response = await client.post(
                f"http://localhost:8000/r2/convo/{stream_sid}",
                json=transcript_data,
                timeout=30.0
            )
            
            if transcript_response.status_code == 200:
                logger.info(f"📤 Uploaded transcript to R2: {stream_sid}")
            else:
                logger.error(f"❌ Failed to upload transcript to R2: {transcript_response.status_code}")
        
        # Prepare risk data for R2
        risk_data = {
            "risk_score": risk_score,
            "risk_band": risk_band,
            "prediction": "scam" if risk_score >= 0.7 else ("suspicious" if risk_score >= 0.4 else "safe"),
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_details": {
                "final_risk_score": risk_score,
                "call_duration": duration,
                "transcript_length": len(complete_transcript)
            }
        }
        
        # Upload risk data to R2
        async with httpx.AsyncClient() as client:
            risk_response = await client.put(
                f"http://localhost:8000/r2/convo/{stream_sid}/risk",
                json=risk_data,
                timeout=30.0
            )
            
            if risk_response.status_code == 200:
                logger.info(f"📊 Uploaded risk data to R2: {stream_sid}")
            else:
                logger.error(f"❌ Failed to upload risk data to R2: {risk_response.status_code}")
        
        # Upload metadata to R2
        metadata = {
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "call_duration": duration,
            "stream_sid": stream_sid,
            "status": "completed",
            "transcript_length": len(complete_transcript),
            "final_risk_score": risk_score,
            "risk_band": risk_band
        }
        
        async with httpx.AsyncClient() as client:
            meta_response = await client.put(
                f"http://localhost:8000/r2/convo/{stream_sid}/meta",
                json=metadata,
                timeout=30.0
            )
            
            if meta_response.status_code == 200:
                logger.info(f"📄 Uploaded metadata to R2: {stream_sid}")
            else:
                logger.error(f"❌ Failed to upload metadata to R2: {meta_response.status_code}")
                
    except Exception as e:
        logger.error(f"❌ R2 push error for {stream_sid}: {e}")
        raise

async def _notify_frontend_async(stream_sid, transcript, analysis):
    """Send frontend notification asynchronously"""
    try:
        await broadcast_to_frontends({
            "event": "update",
            "streamSid": stream_sid,
            "text": transcript,
            "clean_text": transcript,  # Use raw transcript for improved ensemble
            "risk": analysis['ensemble_score'],
            "band": analysis['risk_band'],
            "prediction": analysis['prediction'],
            "timestamp": datetime.utcnow().isoformat(),
            "ensemble_details": {
                "ensemble_score": analysis['ensemble_score'],
                "advanced_score": analysis['advanced_score'],
                "ml_score": analysis['ml_score'],
                "method": analysis['method']
            }
        })
    except Exception as e:
        logger.error(f"❌ Frontend notification error: {e}")

@app.websocket("/media")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Twilio Media Streams with OpenAI Whisper transcription"""
    global current_stream_sid
    try:
        await websocket.accept()
        logger.info("🔌 WebSocket connection established")
        print("🔌 [DEBUG] WebSocket connection established")
    except Exception as e:
        print(f"🔌 [DEBUG] WebSocket accept failed: {e}")
        return
    
    # Real-time processing only - no buffering needed
    
    try:
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
            except Exception as e:
                logger.error(f"WebSocket receive error: {e}")
                break
            
            # Handle different event types
            event = message.get("event", "unknown")
            
            if event == "connected":
                logger.info("📞 Twilio Media Stream connected")
                
            elif event == "start":
                stream_sid = message.get("start", {}).get("streamSid", "unknown")
                logger.info(f"📞 Call started: {stream_sid}")
                # Store stream_sid globally for frontend access
                current_stream_sid = stream_sid
                
                # Initialize call session in active_calls
                active_calls[stream_sid] = []
                
                # Create call session in database
                try:
                    create_call_in_database(stream_sid)
                    logger.info(f"📊 Database session created for {stream_sid}")
                except Exception as e:
                    logger.error(f"❌ Database error: {e}")
                
                # 🚀 Send call start notification to frontend
                await broadcast_to_frontends({
                    "event": "call_start",
                    "streamSid": stream_sid,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Store stream_sid in websocket state
                websocket.state.stream_sid = stream_sid
                # Initialize audio buffer for this stream
                websocket.state.audio_buffer = {}
                # Add Twilio client to audio bridge
                bridge.add_twilio_client(stream_sid, websocket)
                # Reset adaptive risk score for new call
                global recent_risk_score
                recent_risk_score = 0.0
                # Initialize transcript file for new session
                initialize_transcript_file()
                # Initialize analysis file for new session
                with transcript_file_lock:
                    try:
                        with open("live_analysis.txt", "w", encoding="utf-8") as f:
                            f.write("")  # Clear the file
                        logger.info("📄 Initialized live_analysis.txt for new session")
                    except Exception as e:
                        logger.error(f"❌ Failed to initialize analysis file: {e}")
                
            elif event == "media":
                # Buffer audio for proper processing
                payload = message.get("media", {}).get("payload", "")
                if payload:
                    try:
                        # Decode Twilio µ-law payload to PCM16
                        pcm16 = decode_twilio_payload(payload)
                        
                        # Apply noise reduction to improve transcription accuracy
                        pcm16 = denoise_pcm(pcm16)
                        
                        # Broadcast audio to browser clients
                        stream_sid = getattr(websocket.state, 'stream_sid', 'unknown')
                        await bridge.broadcast_to_browser(stream_sid, pcm16)
                        
                        # Add to buffer instead of processing immediately
                        if stream_sid not in websocket.state.audio_buffer:
                            websocket.state.audio_buffer[stream_sid] = []
                        websocket.state.audio_buffer[stream_sid].extend(pcm16)
                        
                        # Check if we have enough audio for processing (5 seconds)
                        if len(websocket.state.audio_buffer[stream_sid]) >= 40000:  # 5 seconds at 8kHz
                            # Process buffered audio
                            buffered_audio_list = websocket.state.audio_buffer[stream_sid][:40000]
                            websocket.state.audio_buffer[stream_sid] = websocket.state.audio_buffer[stream_sid][40000:]
                            
                            # Convert list to bytes for Whisper
                            buffered_audio_bytes = bytes(buffered_audio_list)
                            
                            # Process the buffered audio
                            asyncio.create_task(process_audio_chunk(buffered_audio_bytes, 8000, stream_sid))
                                
                    except Exception as e:
                        logger.error(f"❌ Audio processing error: {e}")
                
            elif event == "stop":
                logger.info("WS: stop event")
                
                # Process any remaining audio in buffer
                stream_sid = getattr(websocket.state, 'stream_sid', 'unknown')
                if hasattr(websocket.state, 'audio_buffer') and stream_sid in websocket.state.audio_buffer:
                    remaining_audio_list = websocket.state.audio_buffer[stream_sid]
                    if len(remaining_audio_list) > 0:
                        logger.info(f"📄 Processing remaining {len(remaining_audio_list)} audio samples")
                        # Convert list to bytes for Whisper
                        remaining_audio_bytes = bytes(remaining_audio_list)
                        asyncio.create_task(process_audio_chunk(remaining_audio_bytes, 8000, stream_sid))
                
                # Clean up audio bridge
                bridge.cleanup_stream(stream_sid)
                
                # Get final risk summary and clean up advanced detection
                final_summary = get_call_risk_summary(stream_sid)
                print(f"[STREAM] Final risk summary: {final_summary}")
                cleanup_call_detection(stream_sid)
                
                # Read complete transcript from live_transcript.txt
                complete_transcript = ""
                try:
                    with open("live_transcript.txt", "r", encoding="utf-8") as f:
                        complete_transcript = f.read().strip()
                    logger.info(f"📄 Read complete transcript: {len(complete_transcript)} characters")
                except Exception as e:
                    logger.error(f"❌ Failed to read live_transcript.txt: {e}")
                    complete_transcript = ""
                
                # Calculate call duration
                call_duration = 0.0  # TODO: Calculate actual call duration
                
                # Determine risk band
                risk_band = "LOW"
                if recent_risk_score >= 0.7:
                    risk_band = "HIGH"
                elif recent_risk_score >= 0.4:
                    risk_band = "MEDIUM"
                
                # Store complete transcript and final risk score in database
                if complete_transcript:
                    try:
                        success = db.add_transcript(
                            stream_sid, 
                            complete_transcript,  # Full transcript
                            recent_risk_score,    # Average risk score
                            risk_band,
                            call_duration
                        )
                        if success:
                            logger.info(f"📊 Stored complete transcript in database for {stream_sid}")
                        else:
                            logger.error(f"❌ Failed to store transcript in database")
                    except Exception as e:
                        logger.error(f"❌ Database error: {e}")
                
                # Complete call in database
                complete_call_in_database(stream_sid, recent_risk_score, risk_band, call_duration)
                
                # 🚀 Push complete transcript and risk data to R2
                if complete_transcript:
                    try:
                        logger.info(f"[R2 PUSH] Using risk score: {recent_risk_score:.3f}, risk band: {risk_band}")
                        await _push_to_r2_async(stream_sid, complete_transcript, recent_risk_score, risk_band, call_duration)
                        logger.info(f"☁️ Pushed complete transcript to R2 for {stream_sid}")
                    except Exception as e:
                        logger.error(f"❌ R2 upload error: {e}")
                
                # Clean up active_calls
                if stream_sid in active_calls:
                    active_calls.pop(stream_sid, None)  # Thread-safe cleanup
                
                # 🚀 Send call end notification to frontend
                await broadcast_to_frontends({
                    "event": "call_end",
                    "streamSid": stream_sid,
                    "final_score": round(recent_risk_score, 2),
                    "duration": call_duration,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Reset global stream_sid
                current_stream_sid = None
                print("[STREAM] Twilio stream stopped")
                
                # Add call end marker to transcript file
                finalize_transcript_file()
                
                logger.info("WS: call ended")
                break
                
            else:
                logger.info(f"📨 Received unknown event: {event}")
            
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket disconnected")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        # Clean up - no buffer needed
        pass

@app.websocket("/browser/{stream_sid}")
async def browser_ws(websocket: WebSocket, stream_sid: str):
    """WebSocket endpoint for browser clients to receive and send audio"""
    await websocket.accept()
    logger.info(f"🌐 Browser client connected to stream: {stream_sid}")
    
    # Add browser client to audio bridge
    bridge.add_browser_client(stream_sid, websocket)
    
    try:
        while True:
            # Receive audio data from browser
            data = await websocket.receive_bytes()
            
            # Broadcast audio to Twilio clients
            await bridge.broadcast_to_twilio(stream_sid, data)
            
    except WebSocketDisconnect:
        logger.info(f"🌐 Browser client disconnected from stream: {stream_sid}")
    except Exception as e:
        logger.error(f"❌ Browser WebSocket error: {e}")
    finally:
        # Remove browser client from audio bridge
        bridge.remove_browser_client(stream_sid, websocket)
        await websocket.close()

@app.websocket("/notify")
async def notify_frontend(websocket: WebSocket):
    """WebSocket endpoint for frontend notifications"""
    await websocket.accept()
    connected_frontends.add(websocket)
    print(f"[WS] Frontend connected: {websocket.client}")
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to ScamShield AI notifications",
            "timestamp": "2024-01-01T00:00:00Z",
            "status": "connected"
        })
        
        # Keep connection alive
        try:
            while True:
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                    await websocket.send_json({
                        "type": "echo",
                        "message": f"Received: {data}",
                        "timestamp": "2024-01-01T00:00:00Z"
                    })
                except asyncio.TimeoutError:
                    continue
                except WebSocketDisconnect:
                    break
        except WebSocketDisconnect:
            print("[WS] Frontend disconnected")
        except Exception as e:
            print(f"[WS ERROR] {e}")
        finally:
            connected_frontends.discard(websocket)
            print("[WS] Frontend disconnected")
    except WebSocketDisconnect:
        print("[WS] Frontend disconnected")
    except Exception as e:
        print(f"[WS ERROR] {e}")
    finally:
        connected_frontends.discard(websocket)
        print("[WS] Frontend disconnected")

@app.websocket("/test")
async def test_websocket(websocket: WebSocket):
    """Test WebSocket endpoint for frontend connection testing"""
    await websocket.accept()
    print(f"[TEST WS] Frontend connected: {websocket.client}")
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "welcome",
            "message": "Connected to ScamShield AI test WebSocket!",
            "timestamp": "2024-01-01T00:00:00Z"
        })
        
        # Send periodic test messages
        counter = 0
        while True:
            await asyncio.sleep(5)  # Send message every 5 seconds
            counter += 1
            
            test_message = {
                "type": "test_message",
                "counter": counter,
                "message": f"Test message #{counter} from ScamShield AI",
                "timestamp": "2024-01-01T00:00:00Z",
                "status": "active"
            }
            
            await websocket.send_json(test_message)
            print(f"[TEST WS] Sent test message #{counter}")
            
    except WebSocketDisconnect:
        print("[TEST WS] Frontend disconnected")
    except Exception as e:
        print(f"[TEST WS ERROR] {e}")
    finally:
        print("[TEST WS] Connection closed")

@app.get("/active-stream")
async def get_active_stream():
    """
    Return the current active Twilio stream SID (if any)
    """
    global current_stream_sid
    print(f"[STREAM] Active stream requested -> {current_stream_sid}")
    
    if current_stream_sid:
        return {"streamSid": current_stream_sid}
    else:
        return {"streamSid": None, "message": "No active stream"}

# Test R2 endpoint removed - no recording needed

@app.post("/transcribe/")
async def transcribe(file: UploadFile = File(...)):
    """Accepts a .wav, .mp3, or similar file and sends it to Whisper."""
    try:
        # Save the uploaded file to a temp path
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Call Whisper API
        with open(tmp_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        return {"success": True, "transcript": response.text}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/analyze/")
async def analyze_transcript(input: TranscriptInput):
    """Analyze a transcript and return scam score + matched keywords."""
    score = scam_score(input.transcript)
    matches = check_keywords(input.transcript)
    return {
        "transcript": input.transcript,
        "scam_score": score,
        "matches": matches
    }

class TextInput(BaseModel):
    text: str

@app.post("/predict/")
async def predict_text(input: TextInput):
    model = get_model()
    result = model.predict(input.text)
    # Determine prediction based on probability
    if result["probability"] < 0.3:
        prediction = "safe"
    elif result["probability"] < 0.7:
        prediction = "suspicious"
    else:
        prediction = "scam"
    
    return {
        "text": input.text,
        "prediction": prediction,
        "probability": result["probability"]
    }
@app.post("/test_transcribe/")
async def test_transcribe(input: TextInput):
    global recent_risk_score
    
    # Use ensemble detector combining AdvancedScamDetector and ML model
    ensemble_result = analyze_with_ensemble(input.text, "test_session")
    
    # Update global risk score with the ensemble score
    recent_risk_score = ensemble_result['ensemble_score']
    
    # Logging
    print(f"[ENSEMBLE] Text: '{input.text[:50]}...'")
    print(f"[ENSEMBLE] Final Score: {ensemble_result['ensemble_score']:.3f} ({ensemble_result['risk_band']})")
    print(f"[ENSEMBLE] Advanced: {ensemble_result['advanced_score']:.3f}, ML: {ensemble_result['ml_score']:.3f}")
    print(f"[ENSEMBLE] Method: {ensemble_result['method']}")
    
    # Write to analysis file with proper format
    with open("live_analysis.txt", "a") as f:
        ts = datetime.utcnow().isoformat()
        f.write(f"{ts} | {input.text} | ensemble={ensemble_result['ensemble_score']:.3f} | advanced={ensemble_result['advanced_score']:.3f} | ml={ensemble_result['ml_score']:.3f} | band={ensemble_result['risk_band']}\n")
    
    return {
        "raw": input.text,
        "clean": input.text.lower().strip(),
        "current_score": ensemble_result['ensemble_score'],
        "recent_risk_score": recent_risk_score,
        "risk_band": ensemble_result['risk_band'],
        "prediction": ensemble_result['prediction'],
        "ensemble_details": {
            "ensemble_score": ensemble_result['ensemble_score'],
            "advanced_score": ensemble_result['advanced_score'],
            "ml_score": ensemble_result['ml_score'],
            "method": ensemble_result['method'],
            "is_trained": ensemble_result['is_trained']
        }
    }

@app.post("/train_ensemble/")
async def train_ensemble_model():
    """Train the ensemble model with sample data"""
    try:
        ensemble_detector = get_ensemble_detector()
        
        # Create sample training data
        training_data = ensemble_detector.create_sample_training_data()
        
        # Train the model
        result = ensemble_detector.train_ensemble(training_data)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Ensemble model trained successfully",
                "accuracy": result["accuracy"],
                "training_samples": result["training_samples"],
                "feature_importance": result["feature_importance"],
                "model_path": result["model_saved_to"]
            }
        else:
            return {
                "success": False,
                "message": result["message"]
            }
            
    except Exception as e:
        logger.error(f"❌ Error training ensemble model: {e}")
        return {
            "success": False,
            "message": f"Training failed: {str(e)}"
        }

@app.post("/quick_evaluate/")
async def quick_model_evaluation():
    """Quick model evaluation with key metrics and edge case testing"""
    try:
        print("🚀 Starting quick model evaluation...")
        
        evaluator = QuickEvaluator()
        results = evaluator.evaluate_quick()
        report = evaluator.generate_quick_report(results)
        print(report)  # Print to console
        
        return {
            "success": True,
            "message": "Quick evaluation completed",
            "report": report,
            "metrics": results.get('metrics', {}),
            "summary": results.get('summary', {}),
            "false_positives": results.get('false_positives', []),
            "false_negatives": results.get('false_negatives', []),
            "model_info": results.get('model_info', {})
        }
        
    except Exception as e:
        logger.error(f"❌ Error in quick evaluation: {e}")
        return {
            "success": False,
            "message": f"Quick evaluation failed: {str(e)}"
        }

@app.post("/evaluate_model/")
async def evaluate_model_comprehensive():
    """Comprehensive model evaluation with AUC/ROC, precision, recall, and edge case testing"""
    try:
        print("🔍 Starting comprehensive model evaluation...")
        
        # Create evaluator and run evaluation
        evaluator = ModelEvaluator()
        results = evaluator.evaluate_model_comprehensive()
        
        # Generate performance report
        report = evaluator.generate_performance_report()
        print(report)  # Print to console
        
        # Save results to file
        evaluator.save_evaluation_results()
        
        return {
            "success": True,
            "message": "Model evaluation completed successfully",
            "report": report,
            "summary": {
                "accuracy": results['overall_metrics']['accuracy'],
                "precision": results['overall_metrics']['precision'],
                "recall": results['overall_metrics']['recall'],
                "f1_score": results['overall_metrics']['f1_score'],
                "roc_auc": results['overall_metrics']['roc_auc'],
                "test_samples": results['test_samples'],
                "model_trained": results['model_trained']
            },
            "edge_case_results": results['edge_case_analysis'],
            "feature_importance": results.get('feature_importance', {}),
            "cross_validation": results.get('cross_validation', {})
        }
        
    except Exception as e:
        logger.error(f"❌ Error in model evaluation: {e}")
        return {
            "success": False,
            "message": f"Evaluation failed: {str(e)}"
        }

@app.post("/improve_model/")
async def improve_model_performance():
    """Analyze model performance and suggest improvements"""
    try:
        # Run evaluation first
        evaluator = ModelEvaluator()
        results = evaluator.evaluate_model_comprehensive()
        
        # Analyze results and suggest improvements
        improvements = []
        metrics = results['overall_metrics']
        
        # Check accuracy
        if metrics['accuracy'] < 0.85:
            improvements.append("Accuracy below 85% - consider more training data")
        
        # Check precision (false positives)
        if metrics['precision'] < 0.8:
            improvements.append("High false positive rate - tune classification threshold")
        
        # Check recall (false negatives)
        if metrics['recall'] < 0.8:
            improvements.append("High false negative rate - improve scam detection sensitivity")
        
        # Check ROC AUC
        if metrics['roc_auc'] < 0.9:
            improvements.append("ROC AUC below 0.9 - improve model discrimination")
        
        # Check edge cases
        edge_results = results['edge_case_analysis']
        for category, result in edge_results.items():
            if isinstance(result, dict) and result.get('accuracy', 1.0) < 0.7:
                improvements.append(f"Poor performance on {category.replace('_', ' ')} - needs attention")
        
        # Generate improved training data suggestions
        training_suggestions = []
        if edge_results.get('ambiguous_cases', {}).get('accuracy', 1.0) < 0.6:
            training_suggestions.append("Add more ambiguous case examples to training data")
        
        if edge_results.get('technical_terms', {}).get('accuracy', 1.0) < 0.7:
            training_suggestions.append("Include more technical scam scenarios in training")
        
        return {
            "success": True,
            "current_performance": {
                "accuracy": metrics['accuracy'],
                "precision": metrics['precision'],
                "recall": metrics['recall'],
                "f1_score": metrics['f1_score'],
                "roc_auc": metrics['roc_auc']
            },
            "improvements_needed": improvements,
            "training_suggestions": training_suggestions,
            "edge_case_analysis": edge_results,
            "recommendations": [
                "Collect more diverse training data",
                "Implement active learning for edge cases",
                "Consider ensemble of multiple models",
                "Fine-tune feature engineering",
                "Implement confidence-based rejection"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error in model improvement analysis: {e}")
        return {
            "success": False,
            "message": f"Improvement analysis failed: {str(e)}"
        }

@app.post("/train_improved_ensemble/")
async def train_improved_ensemble_model():
    """Train the improved ensemble model with enhanced features"""
    try:
        improved_detector = get_improved_ensemble_detector()
        result = improved_detector.train_improved_ensemble()
        
        if result["success"]:
            return {
                "success": True,
                "message": "Improved ensemble model trained successfully",
                "accuracy": result["accuracy"],
                "optimal_threshold": result["optimal_threshold"],
                "training_samples": result["training_samples"],
                "feature_importance": result["feature_importance"]
            }
        else:
            return {
                "success": False,
                "message": result["message"]
            }
            
    except Exception as e:
        logger.error(f"❌ Error training improved ensemble: {e}")
        return {
            "success": False,
            "message": f"Training failed: {str(e)}"
        }

@app.post("/test_improved_ensemble/")
async def test_improved_ensemble(input: TextInput):
    """Test the improved ensemble detector"""
    try:
        # Use improved ensemble detector
        result = analyze_with_improved_ensemble(input.text, "test_session")
        
        return {
            "raw": input.text,
            "clean": input.text.lower().strip(),
            "current_score": result['ensemble_score'],
            "recent_risk_score": result['ensemble_score'],
            "risk_band": result['risk_band'],
            "prediction": result['prediction'],
            "improved_ensemble_details": {
                "ensemble_score": result['ensemble_score'],
                "advanced_score": result['advanced_score'],
                "ml_score": result['ml_score'],
                "method": result['method'],
                "is_trained": result['is_trained'],
                "optimal_threshold": result.get('optimal_threshold', 0.5),
                "feature_importance": result.get('feature_importance', {}),
                "features": result.get('features', [])
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error in improved ensemble test: {e}")
        return {
            "success": False,
            "message": f"Test failed: {str(e)}"
        }

# Upload chunk endpoint removed - no recording needed

# Finalize endpoint removed - no recording needed

# Database integration functions
def create_call_in_database(stream_sid: str):
    """Create a new call session in the database"""
    try:
        success = db.create_call(stream_sid, stream_sid)
        if success:
            print(f"[DB] ✅ Created call session: {stream_sid}")
            return True
        else:
            print(f"[DB] ❌ Call session already exists: {stream_sid}")
            return False
    except Exception as e:
        print(f"[DB] ❌ Error creating call: {e}")
        return False

# Removed store_transcript_in_database - now storing complete transcript only at call end

def complete_call_in_database(stream_sid: str, final_risk_score: float, risk_band: str, duration: float = 0.0):
    """Complete a call session in the database"""
    try:
        success = db.end_call(stream_sid, final_risk_score, risk_band, None, duration)
        if success:
            print(f"[DB] ✅ Completed call {stream_sid}: score={final_risk_score:.2f}, band={risk_band}")
            return True
        else:
            print(f"[DB] ❌ Failed to complete call {stream_sid}")
            return False
    except Exception as e:
        print(f"[DB] ❌ Error completing call: {e}")
        return False

# Database endpoints for frontend
@app.get("/api/calls")
async def get_call_history(limit: int = 50):
    """Get call history for frontend dashboard"""
    try:
        calls = db.get_call_history(limit)
        return {"status": "success", "calls": calls}
    except Exception as e:
        logger.error(f"Error fetching call history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch call history: {str(e)}")

@app.get("/api/calls/{session_id}/transcripts")
async def get_call_transcripts(session_id: str):
    """Get all transcripts for a specific call"""
    try:
        transcripts = db.get_call_transcripts(session_id)
        return {"status": "success", "session_id": session_id, "transcripts": transcripts}
    except Exception as e:
        logger.error(f"Error fetching transcripts for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch transcripts: {str(e)}")

@app.get("/api/calls/{session_id}/transcript")
async def get_call_transcript(session_id: str):
    """Get complete transcript for a call session"""
    try:
        # Get call details from database
        call_data = db.get_call_history()
        call = next((c for c in call_data if c['session_id'] == session_id), None)
        
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Get transcript from database
        transcripts = db.get_call_transcripts(session_id)
        
        if not transcripts:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        # Combine all transcript chunks into complete transcript
        complete_transcript = ""
        for transcript in transcripts:
            # Try both 'transcript' and 'raw_text' fields
            text = transcript.get('transcript') or transcript.get('raw_text', '')
            if text:
                complete_transcript += text + " "
        
        complete_transcript = complete_transcript.strip()
        
        return {
            "session_id": session_id,
            "transcript": complete_transcript,
            "chunks": len(transcripts),
            "call_start": call.get('start_time'),
            "call_end": call.get('end_time'),
            "duration": call.get('duration', 0),
            "risk_score": call.get('average_risk_score', 0),
            "risk_band": call.get('risk_band', 'LOW')
        }
    except Exception as e:
        logger.error(f"❌ Error getting transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/live-transcript")
async def get_live_transcript():
    """Get current live transcript from file"""
    try:
        if not os.path.exists("live_transcript.txt"):
            return {
                "transcript": "",
                "status": "no_active_call",
                "message": "No active call or transcript available"
            }
        
        with open("live_transcript.txt", "r") as f:
            transcript = f.read().strip()
        
        return {
            "transcript": transcript,
            "status": "active_call",
            "timestamp": datetime.utcnow().isoformat(),
            "characters": len(transcript),
            "lines": len(transcript.split('\n')) if transcript else 0
        }
    except Exception as e:
        logger.error(f"❌ Error getting live transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/risk-summary")
async def get_risk_summary(hours: int = 24):
    """Get risk summary for dashboard"""
    try:
        summary = db.get_risk_summary(hours)
        return {"status": "success", "summary": summary}
    except Exception as e:
        logger.error(f"Error fetching risk summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch risk summary: {str(e)}")

# Recording endpoint removed - no recording needed

@app.post("/api/calls/{session_id}/start")
async def start_call_session(session_id: str, stream_sid: str = None):
    """Start a new call session in database"""
    try:
        success = db.create_call(session_id, stream_sid)
        if success:
            return {"status": "success", "message": f"Call session {session_id} started"}
        else:
            return {"status": "error", "message": f"Call session {session_id} already exists"}
    except Exception as e:
        logger.error(f"Error starting call session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start call session: {str(e)}")

@app.post("/api/calls/{session_id}/end")
async def end_call_session(session_id: str, final_risk_score: float, 
                          risk_band: str, duration_seconds: float = None):
    """End a call session in database"""
    try:
        success = db.end_call(session_id, final_risk_score, risk_band, None, duration_seconds)
        if success:
            return {"status": "success", "message": f"Call session {session_id} ended"}
        else:
            return {"status": "error", "message": f"Failed to end call session {session_id}"}
    except Exception as e:
        logger.error(f"Error ending call session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to end call session: {str(e)}")

@app.post("/api/calls/{session_id}/disconnect")
async def disconnect_call(session_id: str):
    """Disconnect/cut a Twilio call"""
    global current_stream_sid
    
    try:
        # Check if this is the active stream
        if current_stream_sid != session_id:
            return {
                "success": False, 
                "message": f"No active call found for session {session_id}",
                "active_stream": current_stream_sid
            }
        
        # Try to disconnect via Twilio API if credentials are available
        call_to_hangup = None
        try:
            import os
            from twilio.rest import Client
            
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            
            if account_sid and auth_token and account_sid != 'your_twilio_account_sid_here':
                # Initialize Twilio client
                client = Client(account_sid, auth_token)
                
                # Find and hang up the call using the stream SID
                calls = client.calls.list(limit=50)  # Get recent calls
                
                for call in calls:
                    # Check if this call has our stream SID in its metadata or properties
                    if hasattr(call, 'stream_sid') and call.stream_sid == session_id:
                        call_to_hangup = call
                        break
                    # Alternative: check if the session_id matches the call SID
                    elif call.sid == session_id:
                        call_to_hangup = call
                        break
                
                if call_to_hangup:
                    # Hang up the call
                    call_to_hangup.update(status='completed')
                    logger.info(f"📞 Twilio call {call_to_hangup.sid} hung up successfully")
                else:
                    logger.warning(f"⚠️ Could not find Twilio call for stream {session_id}")
            else:
                logger.info("⚠️ Twilio credentials not configured - using local disconnect only")
                
        except Exception as twilio_error:
            logger.warning(f"⚠️ Twilio API error: {twilio_error} - using local disconnect only")
        
        # Clean up the stream from audio bridge
        bridge.cleanup_stream(session_id)
        
        # Remove from active calls
        if session_id in active_calls:
            active_calls.pop(session_id, None)
        
        # Reset global stream_sid
        current_stream_sid = None
        
        logger.info(f"📞 Call disconnected by frontend: {session_id}")
        
        return {
            "success": True,
            "message": f"Call {session_id} disconnected successfully",
            "session_id": session_id,
            "twilio_disconnected": call_to_hangup is not None
        }
        
    except Exception as e:
        logger.error(f"Error disconnecting call {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disconnect call: {str(e)}")