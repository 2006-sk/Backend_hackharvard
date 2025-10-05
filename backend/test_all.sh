#!/bin/bash
echo "Testing ScamShield AI Backend..."
echo "1. Health check:"
curl -s http://localhost:8000/health
echo -e "\n\n2. Upload chunks:"
echo "chunk1" | curl -s -X POST -F "audio_chunk=@-" http://localhost:8000/upload_chunk/test123
echo "chunk2" | curl -s -X POST -F "audio_chunk=@-" http://localhost:8000/upload_chunk/test123
echo -e "\n\n3. Finalize session:"
curl -s -X POST http://localhost:8000/finalize/test123
echo -e "\n\n4. Test scam detection:"
curl -s -X POST http://localhost:8000/test_transcribe/ -H "Content-Type: application/json" -d '{"text": "This is officer Davis from the IRS calling about your tax debt"}'
