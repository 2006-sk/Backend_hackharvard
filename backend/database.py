import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

class TranscriptDB:
    def __init__(self, db_path: str = "scamshield.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create calls table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                stream_sid TEXT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                duration_seconds REAL,
                final_risk_score REAL,
                risk_band TEXT,
                r2_audio_url TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Create transcripts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_text TEXT,
                clean_text TEXT,
                risk_score REAL,
                risk_band TEXT,
                fuzzy_score REAL,
                ml_score REAL,
                keywords_found TEXT,
                FOREIGN KEY (session_id) REFERENCES calls (session_id)
            )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_calls_session_id ON calls(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transcripts_session_id ON transcripts(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transcripts_timestamp ON transcripts(timestamp)')
        
        conn.commit()
        conn.close()
    
    def create_call(self, session_id: str, stream_sid: str = None) -> bool:
        """Create a new call record"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO calls (session_id, stream_sid, status)
                VALUES (?, ?, 'active')
            ''', (session_id, stream_sid))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False  # Session already exists
    
    def add_transcript(self, session_id: str, raw_text: str, clean_text: str, 
                      risk_score: float, risk_band: str, fuzzy_score: float = None, 
                      ml_score: float = None, keywords_found: str = None) -> bool:
        """Add a transcript entry"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transcripts (session_id, raw_text, clean_text, risk_score, 
                                      risk_band, fuzzy_score, ml_score, keywords_found)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, raw_text, clean_text, risk_score, risk_band, 
                  fuzzy_score, ml_score, keywords_found))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding transcript: {e}")
            return False
    
    def end_call(self, session_id: str, final_risk_score: float, 
                risk_band: str, r2_audio_url: str = None, duration_seconds: float = None) -> bool:
        """Mark a call as ended with final details"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE calls 
                SET end_time = CURRENT_TIMESTAMP, final_risk_score = ?, 
                    risk_band = ?, r2_audio_url = ?, duration_seconds = ?, status = 'ended'
                WHERE session_id = ?
            ''', (final_risk_score, risk_band, r2_audio_url, duration_seconds, session_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error ending call: {e}")
            return False
    
    def get_call_history(self, limit: int = 50) -> List[Dict]:
        """Get recent call history for frontend"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.session_id, c.stream_sid, c.start_time, c.end_time, 
                   c.duration_seconds, c.final_risk_score, c.risk_band, c.r2_audio_url,
                   COUNT(t.id) as transcript_count
            FROM calls c
            LEFT JOIN transcripts t ON c.session_id = t.session_id
            GROUP BY c.session_id
            ORDER BY c.start_time DESC
            LIMIT ?
        ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'session_id': row[0],
                'stream_sid': row[1],
                'start_time': row[2],
                'end_time': row[3],
                'duration_seconds': row[4],
                'final_risk_score': row[5],
                'risk_band': row[6],
                'r2_audio_url': row[7],
                'transcript_count': row[8]
            })
        
        conn.close()
        return results
    
    def get_call_transcripts(self, session_id: str) -> List[Dict]:
        """Get all transcripts for a specific call"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, raw_text, clean_text, risk_score, risk_band, 
                   fuzzy_score, ml_score, keywords_found
            FROM transcripts
            WHERE session_id = ?
            ORDER BY timestamp ASC
        ''', (session_id,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'timestamp': row[0],
                'raw_text': row[1],
                'clean_text': row[2],
                'risk_score': row[3],
                'risk_band': row[4],
                'fuzzy_score': row[5],
                'ml_score': row[6],
                'keywords_found': row[7]
            })
        
        conn.close()
        return results
    
    def get_risk_summary(self, hours: int = 24) -> Dict:
        """Get risk summary for the last N hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as total_calls,
                AVG(final_risk_score) as avg_risk_score,
                COUNT(CASE WHEN risk_band = 'HIGH' THEN 1 END) as high_risk_calls,
                COUNT(CASE WHEN risk_band = 'MEDIUM' THEN 1 END) as medium_risk_calls,
                COUNT(CASE WHEN risk_band = 'LOW' THEN 1 END) as low_risk_calls
            FROM calls 
            WHERE start_time >= datetime('now', '-{} hours')
        '''.format(hours))
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            'total_calls': row[0],
            'avg_risk_score': row[1],
            'high_risk_calls': row[2],
            'medium_risk_calls': row[3],
            'low_risk_calls': row[4]
        }

# Global database instance
db = TranscriptDB()

