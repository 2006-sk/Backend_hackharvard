#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend Health Check Script
Tests local FastAPI, TwiML endpoint, and Cloudflare tunnel connectivity
"""

import requests
import json
import sys

def check_local_health():
    """Check local FastAPI health endpoint"""
    try:
        print("Checking local FastAPI health...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") == True:
                print("✅ Local FastAPI health check passed")
                return True
            else:
                print("❌ Local health check failed - unexpected response:", data)
                return False
        else:
            print("❌ Local health check failed - status code:", response.status_code)
            return False
            
    except requests.exceptions.RequestException as e:
        print("❌ Local health check failed - connection error:", e)
        return False

def check_twiml_endpoint():
    """Check TwiML voice endpoint"""
    try:
        print("Checking TwiML endpoint...")
        response = requests.post("http://localhost:8000/voice", timeout=5)
        
        if response.status_code == 200:
            content = response.text
            if "<Response>" in content and "<?xml" in content:
                print("✅ TwiML endpoint check passed")
                return True
            else:
                print("❌ TwiML endpoint failed - no valid XML response")
                return False
        else:
            print("❌ TwiML endpoint failed - status code:", response.status_code)
            return False
            
    except requests.exceptions.RequestException as e:
        print("❌ TwiML endpoint failed - connection error:", e)
        return False

def get_cloudflare_url():
    """Get Cloudflare tunnel URL"""
    cloudflare_url = "https://neighborhood-operators-lay-extent.trycloudflare.com"
    print("✅ Cloudflare tunnel URL is:", cloudflare_url)
    return cloudflare_url

def check_cloudflare_health(cloudflare_url):
    """Check if Cloudflare tunnel can reach FastAPI health endpoint"""
    try:
        print("Checking Cloudflare tunnel connectivity to", cloudflare_url + "/health...")
        response = requests.get(cloudflare_url + "/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") == True:
                print("✅ Cloudflare tunnel health check passed")
                return True
            else:
                print("❌ Cloudflare health check failed - unexpected response:", data)
                return False
        else:
            print("❌ Cloudflare health check failed - status code:", response.status_code)
            return False
            
    except requests.exceptions.RequestException as e:
        print("❌ Cloudflare health check failed - connection error:", e)
        return False

def main():
    """Run all backend checks"""
    print("ScamShield AI Backend Health Check (OpenAI Whisper)")
    print("=" * 50)
    
    # Track overall success
    all_passed = True
    
    # Check 1: Local FastAPI health
    if not check_local_health():
        all_passed = False
    
    print()
    
    # Check 2: TwiML endpoint
    if not check_twiml_endpoint():
        all_passed = False
    
    print()
    
    # Check 3: Cloudflare tunnel
    cloudflare_url = get_cloudflare_url()
    if not cloudflare_url:
        all_passed = False
    else:
        print()
        # Check 4: Cloudflare connectivity
        if not check_cloudflare_health(cloudflare_url):
            all_passed = False
    
    print()
    print("=" * 50)
    
    if all_passed:
        print("🎉 All checks passed! Backend is ready for Twilio integration.")
        print("📞 Configure Twilio webhook to:", cloudflare_url + "/voice")
        sys.exit(0)
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()