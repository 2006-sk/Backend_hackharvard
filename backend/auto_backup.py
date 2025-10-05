#!/usr/bin/env python3
"""
Automatic database backup script for ScamShield AI
Runs every 5 minutes and backs up the database to R2
"""

import os
import boto3
from botocore.exceptions import ClientError
import time
from datetime import datetime

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file"""
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        print("⚠️  .env file not found")

# Load environment variables
load_env_file()

# R2 Configuration
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME')
R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID')

def backup_database():
    """Backup database to R2"""
    try:
        # Create R2 client
        r2_client = boto3.client(
            's3',
            endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY
        )
        
        # Database file path
        db_path = "scamshield.db"
        
        if not os.path.exists(db_path):
            print(f"❌ Database file not found: {db_path}")
            return False
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_key = f"database_backups/scamshield_{timestamp}.db"
        
        # Upload database to R2
        with open(db_path, 'rb') as db_file:
            r2_client.upload_fileobj(
                db_file,
                R2_BUCKET_NAME,
                backup_key,
                ExtraArgs={
                    'ContentType': 'application/octet-stream',
                    'Metadata': {
                        'backup_date': timestamp,
                        'description': 'ScamShield AI Database Backup'
                    }
                }
            )
        
        # Also update the latest backup
        latest_key = "database_backups/latest.db"
        with open(db_path, 'rb') as db_file:
            r2_client.upload_fileobj(
                db_file,
                R2_BUCKET_NAME,
                latest_key,
                ExtraArgs={
                    'ContentType': 'application/octet-stream',
                    'Metadata': {
                        'backup_date': timestamp,
                        'description': 'Latest ScamShield AI Database Backup'
                    }
                }
            )
        
        file_size = os.path.getsize(db_path)
        print(f"✅ Database backed up: {backup_key} ({file_size:,} bytes)")
        return True
        
    except ClientError as e:
        print(f"❌ Error backing up database: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    print("🔄 ScamShield AI - Auto Backup Service")
    print("=" * 50)
    print("📅 Starting automatic database backup (every 5 minutes)")
    print("🛑 Press Ctrl+C to stop")
    print()
    
    # Check environment variables
    required_vars = ['R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_BUCKET_NAME', 'R2_ACCOUNT_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return
    
    print(f"📦 R2 Bucket: {R2_BUCKET_NAME}")
    print(f"🏢 Account ID: {R2_ACCOUNT_ID}")
    print()
    
    backup_count = 0
    
    try:
        while True:
            # Perform backup
            success = backup_database()
            if success:
                backup_count += 1
                print(f"📊 Total backups: {backup_count}")
            
            # Wait 5 minutes (300 seconds)
            print(f"⏰ Next backup in 5 minutes... ({datetime.now().strftime('%H:%M:%S')})")
            time.sleep(300)  # 5 minutes
            
    except KeyboardInterrupt:
        print()
        print(f"🛑 Auto backup stopped. Total backups performed: {backup_count}")
        print("✅ Service terminated gracefully")

if __name__ == "__main__":
    main()
