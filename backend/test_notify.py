#!/usr/bin/env python3
"""
Simple test script to test notify functionality
"""

import requests
import json
import asyncio
import websockets
import time

# Server URL
BASE_URL = "https://submammary-correlatively-irma.ngrok-free.dev"

def test_health():
    """Test server health"""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_transcription():
    """Test transcription and notify"""
    print("\n🎙️ Testing transcription endpoint...")
    
    test_cases = [
        {
            "name": "High Risk - IRS Scam",
            "text": "This is the IRS calling about your tax debt. You need to pay immediately or face arrest."
        },
        {
            "name": "Medium Risk - Bank Account",
            "text": "Your bank account has been compromised. Please provide your PIN number immediately."
        },
        {
            "name": "Low Risk - Safe Conversation",
            "text": "Thank you for calling. This is a legitimate business call about your account."
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📝 Testing: {test_case['name']}")
        try:
            response = requests.post(
                f"{BASE_URL}/test_transcribe",
                headers={"Content-Type": "application/json"},
                json={"text": test_case["text"]}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Transcription: {data.get('transcript', 'N/A')}")
                print(f"✅ Risk Score: {data.get('risk_score', 'N/A')}")
                print(f"✅ Risk Band: {data.get('risk_band', 'N/A')}")
                print(f"✅ Prediction: {data.get('prediction', 'N/A')}")
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(1)  # Small delay between tests

async def test_websocket_notify():
    """Test WebSocket notify connection"""
    print("\n🔌 Testing WebSocket notify connection...")
    
    try:
        uri = "wss://submammary-correlatively-irma.ngrok-free.dev/notify"
        print(f"Connecting to: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")
            
            # Send a test message
            test_message = {
                "type": "test",
                "message": "Testing WebSocket connection",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            await websocket.send(json.dumps(test_message))
            print("📤 Test message sent")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                print(f"📥 Response received: {data}")
            except asyncio.TimeoutError:
                print("⏰ No response received within 10 seconds")
            
            # Keep connection alive for a bit to test notifications
            print("⏰ Keeping connection alive for 30 seconds to test notifications...")
            await asyncio.sleep(30)
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

def test_call_endpoints():
    """Test call management endpoints"""
    print("\n📞 Testing call management endpoints...")
    
    # Test call history
    try:
        response = requests.get(f"{BASE_URL}/api/calls")
        if response.status_code == 200:
            calls = response.json()
            print(f"✅ Call history: {len(calls)} calls found")
            for call in calls[:3]:  # Show first 3 calls
                print(f"  📞 {call.get('stream_sid', 'N/A')} - {call.get('risk_band', 'N/A')}")
        else:
            print(f"❌ Call history failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Call history error: {e}")
    
    # Test risk summary
    try:
        response = requests.get(f"{BASE_URL}/api/risk-summary")
        if response.status_code == 200:
            summary = response.json()
            print(f"✅ Risk summary: {summary}")
        else:
            print(f"❌ Risk summary failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Risk summary error: {e}")

async def main():
    """Run all tests"""
    print("🚀 ScamShield AI - Notify Test Suite")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_health():
        print("❌ Server not responding. Check if uvicorn and ngrok are running.")
        return
    
    # Test 2: Transcription endpoints
    test_transcription()
    
    # Test 3: Call management endpoints
    test_call_endpoints()
    
    # Test 4: WebSocket notify
    await test_websocket_notify()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
