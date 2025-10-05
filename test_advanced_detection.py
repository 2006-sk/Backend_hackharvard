#!/usr/bin/env python3
"""
Test script for Advanced Scam Detection Engine
Demonstrates segment buffering, EMA risk evaluation, and fuzzy matching
"""

import time
from app.detector.advanced_scam_detector import analyze_text_segment, get_call_risk_summary, cleanup_call_detection

def test_detection_sequence():
    """Test the detection engine with a realistic conversation sequence"""
    print("🧪 Testing Advanced Scam Detection Engine")
    print("=" * 60)
    
    # Test stream ID
    stream_sid = "MZ_test_12345"
    
    # Test sequence: partial fragments that should be grouped into sentences
    test_fragments = [
        "this is the",           # Fragment 1 - should buffer
        "irs calling you now",   # Fragment 2 - should complete sentence 1
        "about your tax debt",   # Fragment 3 - should complete sentence 2
        "please buy gift cards", # Fragment 4 - should complete sentence 3
        "immediately or face",   # Fragment 5 - should buffer
        "arrest warrant",        # Fragment 6 - should complete sentence 4
        "okay goodbye",          # Fragment 7 - should complete sentence 5 (safe)
        "have a nice day"        # Fragment 8 - should complete sentence 6 (safe)
    ]
    
    print("📝 Processing test fragments:")
    print("-" * 40)
    
    for i, fragment in enumerate(test_fragments, 1):
        print(f"\n{i}. Fragment: '{fragment}'")
        
        # Analyze the fragment
        result = analyze_text_segment(stream_sid, fragment)
        
        # Display results
        if result.get("is_buffering", False):
            print(f"   🔄 Buffering... (Current risk: {result['smoothed_risk']:.3f})")
        else:
            print(f"   📊 Complete segment: '{result['segment']}'")
            print(f"   🎯 Base risk: {result['base_risk']:.3f}")
            print(f"   📈 Smoothed risk: {result['smoothed_risk']:.3f}")
            print(f"   🚨 Risk band: {result['risk_band']}")
            
            if result['high_risk_matches']:
                print(f"   ⚠️  High risk matches: {result['high_risk_matches']}")
            if result['medium_risk_matches']:
                print(f"   ⚡ Medium risk matches: {result['medium_risk_matches']}")
            if result['safe_breaker_matches']:
                print(f"   ✅ Safe breaker matches: {result['safe_breaker_matches']}")
        
        # Small delay to simulate real-time processing
        time.sleep(0.1)
    
    # Get final call summary
    print("\n" + "=" * 60)
    print("📋 Final Call Summary:")
    print("-" * 30)
    
    summary = get_call_risk_summary(stream_sid)
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    # Cleanup
    cleanup_call_detection(stream_sid)
    print("\n✅ Test completed and cleaned up!")

def test_fuzzy_matching():
    """Test fuzzy keyword matching with transcription errors"""
    print("\n🔍 Testing Fuzzy Keyword Matching")
    print("=" * 40)
    
    stream_sid = "MZ_fuzzy_test"
    
    # Test cases with common transcription errors
    test_cases = [
        ("this is the iaes calling", "IRS should be detected"),
        ("your social security number", "SSN should be detected"),
        ("buy itunes gift cards", "Gift cards should be detected"),
        ("arrest warrant issued", "Arrest warrant should be detected"),
        ("thank you goodbye", "Safe breaker should be detected"),
        ("this is a scam call", "Safe breaker should be detected")
    ]
    
    for text, expected in test_cases:
        print(f"\nTesting: '{text}'")
        print(f"Expected: {expected}")
        
        result = analyze_text_segment(stream_sid, text)
        
        print(f"Risk: {result['smoothed_risk']:.3f} ({result['risk_band']})")
        if result['high_risk_matches']:
            print(f"High risk: {result['high_risk_matches']}")
        if result['safe_breaker_matches']:
            print(f"Safe: {result['safe_breaker_matches']}")
    
    cleanup_call_detection(stream_sid)

if __name__ == "__main__":
    test_detection_sequence()
    test_fuzzy_matching()
