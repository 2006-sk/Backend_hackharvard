#!/bin/bash
# Test script for /transcribe/ endpoint with fake base64 audio

echo "🧪 Testing /transcribe/ endpoint with fake base64 audio..."

# Create a simple base64 encoded test (this is just a placeholder - real audio would be longer)
TEST_PAYLOAD="UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="

echo "📤 Sending test payload to /transcribe/..."

curl -X POST http://localhost:8000/transcribe/ \
  -H "Content-Type: application/json" \
  -d "{\"payload\": \"$TEST_PAYLOAD\"}" \
  -v

echo -e "\n✅ Test complete!"
echo "💡 Make sure your server is running: python -m uvicorn app.main:app --reload"
