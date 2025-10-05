import asyncio
from collections import defaultdict

class AudioBridge:
    def __init__(self):
        self.twilio_to_clients = defaultdict(set)
        self.clients_to_twilio = defaultdict(set)

    async def broadcast_to_browser(self, stream_sid: str, audio_chunk: bytes):
        """Broadcast audio chunk from Twilio to all connected browser clients"""
        for ws in list(self.twilio_to_clients[stream_sid]):
            try:
                await ws.send_bytes(audio_chunk)
            except Exception:
                self.twilio_to_clients[stream_sid].discard(ws)

    async def broadcast_to_twilio(self, stream_sid: str, audio_chunk: bytes):
        """Broadcast audio chunk from browser to all connected Twilio streams"""
        for ws in list(self.clients_to_twilio[stream_sid]):
            try:
                await ws.send_bytes(audio_chunk)
            except Exception:
                self.clients_to_twilio[stream_sid].discard(ws)

    def add_browser_client(self, stream_sid: str, websocket):
        """Add a browser client to the stream"""
        self.twilio_to_clients[stream_sid].add(websocket)

    def remove_browser_client(self, stream_sid: str, websocket):
        """Remove a browser client from the stream"""
        self.twilio_to_clients[stream_sid].discard(websocket)

    def add_twilio_client(self, stream_sid: str, websocket):
        """Add a Twilio client to the stream"""
        self.clients_to_twilio[stream_sid].add(websocket)

    def remove_twilio_client(self, stream_sid: str, websocket):
        """Remove a Twilio client from the stream"""
        self.clients_to_twilio[stream_sid].discard(websocket)

    def cleanup_stream(self, stream_sid: str):
        """Clean up all connections for a stream"""
        self.twilio_to_clients.pop(stream_sid, None)
        self.clients_to_twilio.pop(stream_sid, None)

# Global bridge instance
bridge = AudioBridge()
