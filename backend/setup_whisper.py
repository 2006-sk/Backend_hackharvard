#!/usr/bin/env python3
"""
Setup script for ScamShield AI with OpenAI Whisper
"""

import os
import sys

def check_env_file():
    """Check if .env file exists and has OpenAI API key"""
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        return False
    
    with open('.env', 'r') as f:
        content = f.read()
        
    if 'your_openai_api_key_here' in content:
        print("⚠️  Please update .env file with your OpenAI API key")
        print("   Edit .env and replace 'your_openai_api_key_here' with your actual API key")
        return False
    
    if 'OPENAI_API_KEY=' in content and 'your_openai_api_key_here' not in content:
        print("✅ .env file configured")
        return True
    
    print("❌ .env file missing OPENAI_API_KEY")
    return False

def main():
    print("🛡️  ScamShield AI - OpenAI Whisper Setup")
    print("=" * 50)
    
    # Check .env file
    if not check_env_file():
        print("\n📝 To get your OpenAI API key:")
        print("1. Go to https://platform.openai.com/api-keys")
        print("2. Create a new API key")
        print("3. Copy the key and update .env file")
        print("4. Replace 'your_openai_api_key_here' with your actual key")
        sys.exit(1)
    
    print("\n🚀 Setup complete! You can now run:")
    print("   python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("\n🧪 Test with:")
    print("   python3 check_backend.py")

if __name__ == "__main__":
    main()
