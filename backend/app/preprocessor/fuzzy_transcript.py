from rapidfuzz import fuzz

SAFE_BREAKERS = [
    "have a great day",
    "we are ending this call",
    "we will report this",
    "report this incident",
    "we never ask for",
    "official website",
    "thank you goodbye",
    "goodbye",
    "we cannot do that on a call"
    # Removed "fraud department" - it can be used in both scams and legitimate calls
]

def should_break_segment(text: str) -> bool:
    """Check if text contains safe breaker phrases that indicate non-scam content"""
    t = text.lower().strip()
    return any(p in t for p in SAFE_BREAKERS)

def merge_transcripts(chunks, similarity_threshold=80, max_window=3):
    """
    Given a list of transcript chunks (strings),
    merge them into a smoother, coherent transcript.
    Removes duplicates and short overlaps with limited window.
    
    Args:
        chunks: List of transcript strings
        similarity_threshold: Threshold for considering chunks as similar (0-100)
        max_window: Maximum number of recent chunks to consider
    
    Returns:
        Merged transcript string with better context
    """
    window = [c for c in chunks[-max_window:] if c and c.strip()]
    merged = []
    
    for chunk in window:
        if not merged:
            merged.append(chunk.strip())
            continue
            
        # Check if this chunk is too similar to the last merged chunk
        if fuzz.partial_ratio(merged[-1].lower(), chunk.lower()) > similarity_threshold:
            continue  # skip near-duplicate
            
        # If chunk is very short (3 words or less), append to last merged chunk
        if len(chunk.split()) <= 3:
            merged[-1] = (merged[-1] + " " + chunk).strip()
        else:
            merged.append(chunk.strip())
    
    return " ".join(merged)
