"""
Advanced Scam Detection Engine
Implements segment buffering, EMA-based risk evaluation, and fuzzy keyword matching
"""

import re
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from rapidfuzz import fuzz, process

@dataclass
class RiskState:
    """Per-call risk state tracking"""
    current_risk: float = 0.0
    peak_risk: float = 0.0
    last_update: float = 0.0
    segment_count: int = 0
    safe_segments_since_risk: int = 0

@dataclass
class ScamKeywords:
    """Scam keyword patterns with fuzzy matching"""
    high_risk: List[str] = None
    medium_risk: List[str] = None
    safe_breakers: List[str] = None
    
    def __post_init__(self):
        if self.high_risk is None:
            self.high_risk = [
                # Government/Authority Impersonation
                "irs", "internal revenue service", "tax debt", "arrest warrant",
                "social security", "ssn", "social security number", "suspended",
                "warrant", "arrest", "police", "fbi", "federal", "court",
                "lawsuit", "legal action", "government officer", "federal agent",
                
                # Urgency/Pressure Tactics
                "immediate payment", "urgent", "asap", "right now", "today",
                "immediately", "expires today", "final warning", "last chance",
                "don't hang up", "stay on the line", "this is urgent",
                
                # Payment Methods (Scam Indicators)
                "gift card", "itunes", "google play", "amazon gift card",
                "bitcoin", "cryptocurrency", "wire transfer", "western union", 
                "money gram", "wire me", "send money", "transfer money",
                "pay with gift card", "buy gift card", "load gift card",
                
                # Financial Information Requests
                "bank account", "routing number", "account number", "pin",
                "verification code", "one time password", "otp", "security code",
                "credit card number", "debit card", "atm pin", "online banking",
                "phone number and otp", "receive an otp", "otp on your phone",
                "provide phone number", "tell me your phone number", "odp",
                "last four digits", "tell me your", "text odp", "sending you a text",
                
                # Threats/Security Claims
                "compromised", "hacked", "breach", "scam", "phishing",
                "account will be closed", "funds will be seized", "wage garnishment",
                "property seizure", "criminal charges", "jail time",
                
                # Money Amounts with Urgency
                "pay $", "send $", "wire $", "transfer $", "owe $",
                "fine of $", "fee of $", "penalty of $", "charge of $",
                
                # Lottery/Prize/Gift Scams
                "congratulations", "you won", "lottery winner", "prize money",
                "claim your prize", "processing fee", "tax on winnings",
                "offer you a gift", "gift of", "thousand dollars gift",
                "amazon gift", "gift from amazon", "amazon services gift",
                "gift coupon", "worth of gifts", "redeem that gift", "selected from",
                "competitive pool", "10,000", "ten thousand",
                
                # Tech Support Scams
                "microsoft support", "apple support", "amazon support",
                "your computer has a virus", "malware detected", "remote access",
                "install software", "download now", "click this link",
                
                # Identity Theft
                "verify your identity", "confirm your identity", "prove who you are",
                "social security fraud", "identity theft", "stolen identity"
            ]
        
        if self.medium_risk is None:
            self.medium_risk = [
                "government", "official", "department", "agency", "authority",
                "compliance", "violation", "penalty", "fine", "fee", "charge",
                "overdue", "past due", "expired", "renewal", "update",
                "verify", "confirm", "validate", "authenticate", "identity"
            ]
        
        if self.safe_breakers is None:
            self.safe_breakers = [
                "thank you", "goodbye", "have a nice day", "take care",
                "bye", "see you later", "talk to you soon",
                "no thank you", "not interested", "remove me", "unsubscribe",
                "this is a scam", "i know this is fake", "i'm hanging up"
                # Removed "fraud department" - it can be used in both scams and legitimate calls
            ]

class SegmentBuffer:
    """Smart sentence segmentation buffer that intelligently groups fragments"""
    
    def __init__(self, max_buffer_time: float = 2.0, min_segment_length: int = 2):
        self.max_buffer_time = max_buffer_time
        self.min_segment_length = min_segment_length
        self.buffer: List[Tuple[str, float]] = []  # (text, timestamp)
        self.last_add_time = 0.0
        self.pending_sentences: List[str] = []  # Store complete sentences
        self.current_sentence = ""  # Current incomplete sentence
    
    def add_fragment(self, text: str) -> Optional[str]:
        """
        Smart sentence segmentation - intelligently groups fragments into complete sentences
        Returns complete sentence if ready, None if still building
        """
        current_time = time.time()
        clean_text = self._clean_text(text)
        
        if not clean_text:
            return None
        
        # Add to buffer with timestamp
        self.buffer.append((clean_text, current_time))
        self.last_add_time = current_time
        
        # Update current sentence
        self.current_sentence = ' '.join([item[0] for item in self.buffer])
        
        # Check for sentence boundaries
        complete_sentence = self._extract_complete_sentence()
        if complete_sentence:
            # Remove the complete sentence from buffer
            self._remove_processed_text(complete_sentence)
            return complete_sentence
        
        # Check if we should force flush (timeout or too long)
        if self._should_force_flush():
            if self.current_sentence.strip():
                sentence = self.current_sentence.strip()
                self.buffer.clear()
                self.current_sentence = ""
                return sentence
        
        return None
    
    def check_timeout(self) -> Optional[str]:
        """Check if buffer should be flushed due to timeout"""
        if not self.buffer:
            return None
        
        current_time = time.time()
        time_since_last = current_time - self.last_add_time
        
        # Force flush if enough time has passed
        if time_since_last >= self.max_buffer_time:
            if self.current_sentence.strip():
                sentence = self.current_sentence.strip()
                self.buffer.clear()
                self.current_sentence = ""
                return sentence
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip().lower())
        
        # Remove common filler words that don't add meaning
        filler_words = ['um', 'uh', 'er', 'ah', 'like', 'you know', 'i mean']
        for filler in filler_words:
            text = text.replace(f' {filler} ', ' ')
        
        return text.strip()
    
    def _extract_complete_sentence(self) -> Optional[str]:
        """Extract complete sentence from current buffer if sentence boundary detected"""
        if not self.current_sentence:
            return None
        
        # Look for sentence endings (punctuation)
        sentence_endings = ['.', '!', '?']
        for ending in sentence_endings:
            if ending in self.current_sentence:
                # Find the last occurrence of the ending
                last_end = self.current_sentence.rfind(ending)
                if last_end != -1:
                    # Extract complete sentence up to the ending
                    complete_sentence = self.current_sentence[:last_end + 1].strip()
                    if len(complete_sentence) >= self.min_segment_length:
                        return complete_sentence
        
        # Look for natural speech boundaries (phrases that sound complete)
        # Common speech patterns that indicate sentence completion
        speech_boundaries = [
            'and i', 'but i', 'so i', 'then i', 'now i', 'well i',
            'and we', 'but we', 'so we', 'then we', 'now we', 'well we',
            'and you', 'but you', 'so you', 'then you', 'now you', 'well you',
            'and they', 'but they', 'so they', 'then they', 'now they', 'well they',
            'and that', 'but that', 'so that', 'then that', 'now that', 'well that',
            'and this', 'but this', 'so this', 'then this', 'now this', 'well this'
        ]
        
        # Check for speech boundaries that indicate a new thought/sentence
        words = self.current_sentence.lower().split()
        for i in range(1, len(words)):
            phrase = ' '.join(words[i-1:i+1])
            if phrase in speech_boundaries and i >= 3:  # At least 3 words before boundary
                # Extract sentence up to the boundary
                complete_sentence = ' '.join(words[:i]).strip()
                if len(complete_sentence) >= self.min_segment_length:
                    return complete_sentence
        
        return None
    
    def _remove_processed_text(self, processed_text: str):
        """Remove processed text from buffer"""
        if not processed_text or not self.buffer:
            return
        
        # Calculate how much text to remove
        words_to_remove = len(processed_text.split())
        current_words = self.current_sentence.split()
        
        if words_to_remove >= len(current_words):
            # Remove all buffer content
            self.buffer.clear()
            self.current_sentence = ""
        else:
            # Remove partial content from buffer
            remaining_words = current_words[words_to_remove:]
            remaining_text = ' '.join(remaining_words)
            
            # Rebuild buffer with remaining text
            self.buffer = [(remaining_text, time.time())]
            self.current_sentence = remaining_text
    
    def _should_force_flush(self) -> bool:
        """Check if we should force flush the buffer"""
        if not self.buffer:
            return False
        
        current_time = time.time()
        time_since_last = current_time - self.last_add_time
        
        # Force flush if enough time has passed
        if time_since_last >= self.max_buffer_time:
            return True
        
        # Force flush if buffer is getting too long
        if len(self.current_sentence) > 150:
            return True
        
        # Force flush if we have enough words (reduced for better sentence formation)
        word_count = len(self.current_sentence.split())
        if word_count >= 5:
            return True
        
        return False
    

class AdvancedScamDetector:
    """
    Advanced scam detection with segment buffering, EMA risk evaluation, and fuzzy matching
    """
    
    def __init__(self, 
                 ema_alpha: float = 0.3,
                 decay_rate: float = 0.115,
                 risk_threshold: float = 0.6,
                 fuzzy_threshold: int = 75):  # Increased from 50 to 75 for more precise matching
        self.ema_alpha = ema_alpha  # EMA smoothing factor (0-1, higher = more responsive)
        self.decay_rate = decay_rate  # Decay rate for safe segments
        self.risk_threshold = risk_threshold  # Threshold for high risk
        self.fuzzy_threshold = fuzzy_threshold  # Fuzzy matching threshold (0-100)
        
        self.keywords = ScamKeywords()
        self.call_states: Dict[str, RiskState] = {}  # Per-call risk states
        self.segment_buffers: Dict[str, SegmentBuffer] = {}  # Per-call segment buffers
    
    def analyze_segment(self, stream_sid: str, raw_text: str) -> Dict:
        """
        Analyze a text segment for scam indicators
        Returns analysis results with risk score and details
        """
        # Initialize call state if new
        if stream_sid not in self.call_states:
            self.call_states[stream_sid] = RiskState()
            self.segment_buffers[stream_sid] = SegmentBuffer()
        
        # Add fragment to buffer and get complete segment if ready
        complete_segment = self.segment_buffers[stream_sid].add_fragment(raw_text)
        
        # If we have a complete segment, process it
        if complete_segment:
            print(f"[DETECTOR] Processing complete segment: '{complete_segment}'")
            analysis = self._analyze_complete_segment(stream_sid, complete_segment)
            self._update_call_state(stream_sid, analysis)
            return analysis
        
        # If still buffering, return current state without processing partial text
        # This prevents broken fragments from being analyzed by the ML model
        print(f"[DETECTOR] Still buffering segment: '{raw_text}'")
        return self._get_current_analysis(stream_sid, raw_text, is_buffering=True)
    
    def _analyze_complete_segment(self, stream_sid: str, segment: str) -> Dict:
        """Analyze a complete text segment for scam indicators"""
        # Fuzzy keyword matching
        high_risk_matches = self._fuzzy_keyword_match(segment, self.keywords.high_risk)
        medium_risk_matches = self._fuzzy_keyword_match(segment, self.keywords.medium_risk)
        safe_breaker_matches = self._fuzzy_keyword_match(segment, self.keywords.safe_breakers)
        
        # Calculate base risk score
        base_risk = self._calculate_base_risk(high_risk_matches, medium_risk_matches, safe_breaker_matches)
        
        # Apply EMA smoothing with previous risk
        current_state = self.call_states[stream_sid]
        if current_state.segment_count == 0:
            # First segment
            smoothed_risk = base_risk
        else:
            # EMA: new_risk = alpha * base_risk + (1 - alpha) * previous_risk
            smoothed_risk = (self.ema_alpha * base_risk + 
                           (1 - self.ema_alpha) * current_state.current_risk)
        
        # Apply decay if safe segment detected
        if safe_breaker_matches or base_risk < 0.1:
            current_state.safe_segments_since_risk += 1
            # Gradual decay: risk = risk * (1 - decay_rate)^safe_segments
            decay_factor = (1 - self.decay_rate) ** min(current_state.safe_segments_since_risk, 5)
            smoothed_risk = smoothed_risk * decay_factor
        else:
            current_state.safe_segments_since_risk = 0
        
        # Ensure risk is bounded between 0 and 1
        smoothed_risk = max(0.0, min(1.0, smoothed_risk))
        
        # Determine risk band
        risk_band = self._get_risk_band(smoothed_risk)
        
        return {
            "segment": segment,
            "raw_text": segment,
            "base_risk": round(base_risk, 3),
            "smoothed_risk": round(smoothed_risk, 3),
            "risk_band": risk_band,
            "high_risk_matches": high_risk_matches,
            "medium_risk_matches": medium_risk_matches,
            "safe_breaker_matches": safe_breaker_matches,
            "is_safe_segment": bool(safe_breaker_matches),
            "segment_count": current_state.segment_count + 1,
            "timestamp": time.time()
        }
    
    def _fuzzy_keyword_match(self, text: str, keywords: List[str]) -> List[str]:
        """Find fuzzy matches for keywords in text with context awareness"""
        if not text or not keywords:
            return []
        
        matches = []
        text_lower = text.lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            
            # Use different matching strategies based on keyword type
            if keywords == self.keywords.safe_breakers:
                # Safe breakers need exact phrase matching (higher threshold)
                threshold = 85
                score = fuzz.partial_ratio(keyword_lower, text_lower)
            elif keywords == self.keywords.high_risk:
                # High risk keywords - be more aggressive for scam detection
                threshold = 65  # Lowered from 80 to catch more patterns
                score = fuzz.partial_ratio(keyword_lower, text_lower)
                
                # Special handling for money amounts and phone/OTP patterns
                if any(money_word in keyword_lower for money_word in ['$', 'dollar', 'money', 'thousand']):
                    threshold = 60  # Even lower for money-related keywords
                elif any(phone_word in keyword_lower for phone_word in ['phone', 'otp', 'number']):
                    threshold = 60  # Lower for phone/OTP keywords
                elif any(gift_word in keyword_lower for gift_word in ['gift', 'coupon', 'amazon']):
                    threshold = 60  # Lower for gift-related keywords
                
                # Additional check: keyword should be a significant part of a word
                if score >= threshold and len(keyword_lower.split()) == 1:
                    # For single words, require they appear as whole words or strong partial matches
                    words = text_lower.split()
                    word_matches = [word for word in words if fuzz.ratio(keyword_lower, word) >= 60]  # Lowered from 70
                    if not word_matches and score < 85:  # Lowered from 90
                        continue  # Skip if it's not a strong word match
            else:
                # Medium risk keywords use standard threshold
                threshold = self.fuzzy_threshold
                score = fuzz.partial_ratio(keyword_lower, text_lower)
            
            if score >= threshold:
                matches.append(f"{keyword} ({score}%)")
        
        return matches
    
    def _calculate_base_risk(self, high_risk_matches: List[str], 
                           medium_risk_matches: List[str], 
                           safe_breaker_matches: List[str]) -> float:
        """Calculate base risk score from keyword matches"""
        # Safe breakers override everything
        if safe_breaker_matches:
            return 0.0
        
        # High risk keywords have strong weight
        high_risk_score = min(len(high_risk_matches) * 0.4, 1.0)
        
        # Medium risk keywords have moderate weight
        medium_risk_score = min(len(medium_risk_matches) * 0.2, 0.6)
        
        # Combine scores (high risk can override medium risk)
        base_risk = max(high_risk_score, medium_risk_score)
        
        # Apply diminishing returns for multiple matches
        if len(high_risk_matches) > 1:
            base_risk = min(base_risk + 0.2, 1.0)
        
        return base_risk
    
    def _get_risk_band(self, risk_score: float) -> str:
        """Convert risk score to risk band"""
        if risk_score < 0.3:
            return "LOW"
        elif risk_score < 0.7:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _update_call_state(self, stream_sid: str, analysis: Dict):
        """Update the call's risk state with new analysis"""
        state = self.call_states[stream_sid]
        
        # Update risk scores
        state.current_risk = analysis["smoothed_risk"]
        state.peak_risk = max(state.peak_risk, state.current_risk)
        state.last_update = analysis["timestamp"]
        state.segment_count = analysis["segment_count"]
    
    def _get_current_analysis(self, stream_sid: str, raw_text: str, is_buffering: bool = False) -> Dict:
        """Get current analysis state (used when still buffering)"""
        state = self.call_states.get(stream_sid, RiskState())
        
        return {
            "segment": raw_text,
            "raw_text": raw_text,
            "base_risk": 0.0,
            "smoothed_risk": state.current_risk,
            "risk_band": self._get_risk_band(state.current_risk),
            "high_risk_matches": [],
            "medium_risk_matches": [],
            "safe_breaker_matches": [],
            "is_safe_segment": False,
            "is_buffering": is_buffering,
            "segment_count": state.segment_count,
            "timestamp": time.time()
        }
    
    def get_call_summary(self, stream_sid: str) -> Dict:
        """Get summary of call's risk analysis"""
        if stream_sid not in self.call_states:
            return {"error": "Call not found"}
        
        state = self.call_states[stream_sid]
        return {
            "stream_sid": stream_sid,
            "current_risk": round(state.current_risk, 3),
            "peak_risk": round(state.peak_risk, 3),
            "segment_count": state.segment_count,
            "safe_segments_since_risk": state.safe_segments_since_risk,
            "last_update": state.last_update,
            "risk_band": self._get_risk_band(state.current_risk)
        }
    
    def cleanup_call(self, stream_sid: str):
        """Clean up call state when call ends"""
        self.call_states.pop(stream_sid, None)
        self.segment_buffers.pop(stream_sid, None)

# Global detector instance
detector = AdvancedScamDetector()

def analyze_text_segment(stream_sid: str, text: str) -> Dict:
    """Main function to analyze text segments - replaces old detection logic"""
    return detector.analyze_segment(stream_sid, text)

def get_call_risk_summary(stream_sid: str) -> Dict:
    """Get risk summary for a call"""
    return detector.get_call_summary(stream_sid)

def cleanup_call_detection(stream_sid: str):
    """Clean up detection state for a call"""
    detector.cleanup_call(stream_sid)

def test_smart_segmentation():
    """Test the smart sentence segmentation logic"""
    print("🧪 Testing Smart Sentence Segmentation")
    print("=" * 50)
    
    # Create a test buffer
    buffer = SegmentBuffer()
    
    # Test case 1: Complete sentence
    result1 = buffer.add_fragment("I am a murderer.")
    print(f"Input: 'I am a murderer.'")
    print(f"Output: {result1}")
    print()
    
    # Test case 2: Partial sentence
    result2 = buffer.add_fragment("I am")
    print(f"Input: 'I am'")
    print(f"Output: {result2}")
    print()
    
    # Test case 3: Complete the sentence
    result3 = buffer.add_fragment("a murderer.")
    print(f"Input: 'a murderer.'")
    print(f"Output: {result3}")
    print()
    
    # Test case 4: New sentence starts
    result4 = buffer.add_fragment("Next sentence")
    print(f"Input: 'Next sentence'")
    print(f"Output: {result4}")
    print()
    
    # Test case 5: Complete second sentence
    result5 = buffer.add_fragment("starts here.")
    print(f"Input: 'starts here.'")
    print(f"Output: {result5}")
    print()
    
    print("✅ Smart segmentation test complete!")

if __name__ == "__main__":
    test_smart_segmentation()
