#!/usr/bin/env python3
"""
R2 Database Backup Script
Backs up SQLite database to Cloudflare R2 storage
"""

import os
import sqlite3
import boto3
from datetime import datetime
import tempfile

# R2 Configuration
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")

def create_r2_client():
    """Create R2 S3 client"""
    if not all([R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, R2_ACCOUNT_ID]):
        raise ValueError("Missing R2 credentials in environment variables")
    
    return boto3.client(
        's3',
        endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY
    )

def backup_database_to_r2():
    """Backup SQLite database to R2"""
    try:
        # Create R2 client
        r2_client = create_r2_client()
        
        # Database file path
        db_path = "scam_calls.db"
        
        if not os.path.exists(db_path):
            print(f"❌ Database file not found: {db_path}")
            return False
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"database_backups/scam_calls_{timestamp}.db"
        
        # Upload to R2
        print(f"📤 Uploading database backup to R2...")
        r2_client.upload_file(db_path, R2_BUCKET_NAME, backup_filename)
        
        # Generate signed URL for download (valid for 1 hour)
        signed_url = r2_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': R2_BUCKET_NAME, 'Key': backup_filename},
            ExpiresIn=3600
        )
        
        print(f"✅ Database backup successful!")
        print(f"📁 Backup file: {backup_filename}")
        print(f"🔗 Download URL: {signed_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def restore_database_from_r2(backup_filename: str):
    """Restore database from R2 backup"""
    try:
        # Create R2 client
        r2_client = create_r2_client()
        
        # Download from R2
        print(f"📥 Downloading database backup from R2...")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
            r2_client.download_file(R2_BUCKET_NAME, backup_filename, temp_file.name)
            
            # Replace current database
            if os.path.exists("scam_calls.db"):
                os.remove("scam_calls.db")
            
            os.rename(temp_file.name, "scam_calls.db")
        
        print(f"✅ Database restore successful!")
        print(f"📁 Restored from: {backup_filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False

def list_database_backups():
    """List all database backups in R2"""
    try:
        r2_client = create_r2_client()
        
        response = r2_client.list_objects_v2(
            Bucket=R2_BUCKET_NAME,
            Prefix="database_backups/"
        )
        
        backups = []
        for obj in response.get('Contents', []):
            backups.append({
                'filename': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified']
            })
        
        print(f"📋 Found {len(backups)} database backups:")
        for backup in sorted(backups, key=lambda x: x['last_modified'], reverse=True):
            print(f"  • {backup['filename']} ({backup['size']} bytes) - {backup['last_modified']}")
        
        return backups
        
    except Exception as e:
        print(f"❌ Failed to list backups: {e}")
        return []

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python r2_database_backup.py backup          # Create backup")
        print("  python r2_database_backup.py restore <file>  # Restore from backup")
        print("  python r2_database_backup.py list            # List backups")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "backup":
        backup_database_to_r2()
    elif command == "restore":
        if len(sys.argv) < 3:
            print("❌ Please provide backup filename")
            sys.exit(1)
        restore_database_from_r2(sys.argv[2])
    elif command == "list":
        list_database_backups()
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)
