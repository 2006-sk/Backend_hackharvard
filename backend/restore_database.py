#!/usr/bin/env python3
"""
Script to restore SQLite database from Cloudflare R2
"""

import os
import boto3
from botocore.exceptions import ClientError
import shutil
from datetime import datetime

# R2 Configuration
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME')
R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID')

def list_database_backups():
    """List available database backups in R2"""
    print("📋 Available database backups:")
    
    try:
        r2_client = boto3.client(
            's3',
            endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY
        )
        
        response = r2_client.list_objects_v2(
            Bucket=R2_BUCKET_NAME,
            Prefix='database_backups/'
        )
        
        backups = []
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'].endswith('.db'):
                    backups.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified']
                    })
        
        if backups:
            for i, backup in enumerate(backups, 1):
                size_mb = backup['size'] / (1024 * 1024)
                print(f"  {i}. {backup['key']} ({size_mb:.2f} MB) - {backup['last_modified']}")
        else:
            print("  📭 No database backups found")
            
        return backups
        
    except ClientError as e:
        print(f"❌ Error listing backups: {e}")
        return []

def restore_database(backup_key):
    """Restore database from R2 backup"""
    print(f"🔄 Restoring database from: {backup_key}")
    
    try:
        r2_client = boto3.client(
            's3',
            endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY
        )
        
        # Local database path
        db_path = "scamshield.db"
        
        # Create backup of current database if it exists
        if os.path.exists(db_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"scamshield_backup_{timestamp}.db"
            shutil.copy2(db_path, backup_path)
            print(f"  💾 Current database backed up to: {backup_path}")
        
        # Download and restore database
        with open(db_path, 'wb') as db_file:
            r2_client.download_fileobj(R2_BUCKET_NAME, backup_key, db_file)
        
        file_size = os.path.getsize(db_path)
        print(f"  ✅ Database restored successfully!")
        print(f"  📊 Restored database size: {file_size:,} bytes")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error restoring database: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    print("🔄 ScamShield AI - Database Restore Script")
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
    
    # List available backups
    backups = list_database_backups()
    
    if not backups:
        print("❌ No backups available to restore")
        return
    
    print()
    
    # For automation, restore the latest backup
    latest_backup = None
    for backup in backups:
        if backup['key'] == 'database_backups/latest.db':
            latest_backup = backup
            break
    
    if latest_backup:
        print("🔄 Restoring latest backup...")
        success = restore_database(latest_backup['key'])
        if success:
            print("✅ Database restore complete!")
        else:
            print("❌ Database restore failed!")
    else:
        print("❌ No latest backup found")
    
    print()
    print("💡 To restore a specific backup, modify this script or use the boto3 client directly")

if __name__ == "__main__":
    main()
