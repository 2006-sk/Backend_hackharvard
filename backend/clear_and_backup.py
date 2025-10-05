#!/usr/bin/env python3
"""
Script to clear R2 bucket and backup SQLite database to Cloudflare R2
"""

import os
import boto3
from botocore.exceptions import ClientError
import sqlite3
from datetime import datetime
import tempfile

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

def clear_r2_bucket():
    """Clear all objects from R2 bucket"""
    print("🗑️  Clearing R2 bucket...")
    
    try:
        # Create R2 client
        r2_client = boto3.client(
            's3',
            endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY
        )
        
        # List all objects
        response = r2_client.list_objects_v2(Bucket=R2_BUCKET_NAME)
        
        if 'Contents' in response:
            objects_to_delete = []
            for obj in response['Contents']:
                objects_to_delete.append({'Key': obj['Key']})
                print(f"  📄 Found: {obj['Key']}")
            
            # Delete all objects
            if objects_to_delete:
                delete_response = r2_client.delete_objects(
                    Bucket=R2_BUCKET_NAME,
                    Delete={
                        'Objects': objects_to_delete,
                        'Quiet': False
                    }
                )
                print(f"  ✅ Deleted {len(objects_to_delete)} objects")
                
                if 'Errors' in delete_response:
                    for error in delete_response['Errors']:
                        print(f"  ❌ Error deleting {error['Key']}: {error['Message']}")
            else:
                print("  📭 Bucket is already empty")
        else:
            print("  📭 Bucket is empty")
            
    except ClientError as e:
        print(f"❌ Error clearing bucket: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def backup_database_to_r2():
    """Backup SQLite database to R2"""
    print("💾 Backing up database to R2...")
    
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
            return
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_key = f"database_backups/scam_calls_{timestamp}.db"
        
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
        
        print(f"  ✅ Database backed up to: {backup_key}")
        
        # Also create a "latest" backup
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
        
        print(f"  ✅ Latest backup created: {latest_key}")
        
        # Get file size
        file_size = os.path.getsize(db_path)
        print(f"  📊 Database size: {file_size:,} bytes")
        
    except ClientError as e:
        print(f"❌ Error backing up database: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def list_r2_contents():
    """List current R2 bucket contents"""
    print("📋 Current R2 bucket contents:")
    
    try:
        r2_client = boto3.client(
            's3',
            endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY
        )
        
        response = r2_client.list_objects_v2(Bucket=R2_BUCKET_NAME)
        
        if 'Contents' in response:
            for obj in response['Contents']:
                size_mb = obj['Size'] / (1024 * 1024)
                print(f"  📄 {obj['Key']} ({size_mb:.2f} MB) - {obj['LastModified']}")
        else:
            print("  📭 Bucket is empty")
            
    except ClientError as e:
        print(f"❌ Error listing bucket contents: {e}")

def main():
    print("🚀 ScamShield AI - R2 Management Script")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ['R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_BUCKET_NAME', 'R2_ACCOUNT_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        return
    
    print(f"📦 R2 Bucket: {R2_BUCKET_NAME}")
    print(f"🏢 Account ID: {R2_ACCOUNT_ID}")
    print()
    
    # Show current contents
    list_r2_contents()
    print()
    
    # Clear bucket
    clear_r2_bucket()
    print()
    
    # Backup database
    backup_database_to_r2()
    print()
    
    # Show final contents
    print("📋 Final R2 bucket contents:")
    list_r2_contents()
    
    print()
    print("✅ R2 management complete!")

if __name__ == "__main__":
    main()
