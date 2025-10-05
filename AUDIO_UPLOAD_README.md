# Audio Upload and Cloudflare R2 Integration

This document describes the new audio chunk upload and Cloudflare R2 storage functionality added to the ScamShield AI backend.

## New Endpoints

### 1. POST `/upload_chunk/{session_id}`
Uploads an audio chunk for a specific session.

**Request:**
- `session_id` (path parameter): Unique identifier for the session
- `audio_chunk` (file upload): Binary audio data

**Response:**
```json
{
  "status": "success",
  "session_id": "abc123",
  "chunk_size": 32000,
  "total_chunks": 5
}
```

### 2. POST `/finalize/{session_id}`
Combines all chunks for a session into a WAV file and uploads to Cloudflare R2.

**Request:**
- `session_id` (path parameter): Unique identifier for the session

**Response:**
```json
{
  "status": "success",
  "session_id": "abc123",
  "url": "https://bucket.account.r2.cloudflarestorage.com/audio_abc123.wav",
  "filename": "audio_abc123.wav",
  "size_bytes": 160000
}
```

## WebSocket Notifications

When a session is finalized, a notification is sent to all connected frontend clients via the existing `/notify` WebSocket:

```json
{
  "event": "audio_ready",
  "session_id": "abc123",
  "url": "https://bucket.account.r2.cloudflarestorage.com/audio_abc123.wav",
  "filename": "audio_abc123.wav",
  "size_bytes": 160000
}
```

## Environment Variables

Add these to your `.env` file:

```bash
# Cloudflare R2 Configuration
R2_ACCESS_KEY_ID=your_r2_access_key_id_here
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key_here
R2_BUCKET_NAME=your_r2_bucket_name_here
R2_ACCOUNT_ID=your_r2_account_id_here
```

## Audio Format

- **Format**: WAV
- **Channels**: 1 (mono)
- **Sample Rate**: 16000 Hz
- **Bit Depth**: 16-bit PCM

## Error Handling

- **400 Bad Request**: No audio chunks found for the session
- **500 Internal Server Error**: Upload or R2 storage failure

## Testing

Use the provided `test_audio_upload.py` script to test the functionality:

```bash
python test_audio_upload.py
```

## Dependencies

The following dependency has been added to `requirements.txt`:
- `boto3==1.34.0` (for Cloudflare R2 S3-compatible API)

## Implementation Details

- Audio chunks are stored in memory using a thread-safe dictionary
- Chunks are combined using the Python `wave` module
- Cloudflare R2 is accessed via the S3-compatible API using boto3
- Local temporary files are automatically cleaned up after upload
- All operations are logged for debugging and monitoring

