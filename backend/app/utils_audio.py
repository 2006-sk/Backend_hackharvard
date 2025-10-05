import base64
import audioop

def decode_twilio_payload(payload_b64: str) -> bytes:
    """
    Convert Twilio Media Stream base64 µ-law audio into PCM16 bytes.
    Twilio sends 8kHz µ-law, mono. This returns 16-bit linear PCM.
    """
    mulaw_bytes = base64.b64decode(payload_b64)
    pcm16 = audioop.ulaw2lin(mulaw_bytes, 2)  # 2 bytes = 16-bit samples
    return pcm16
