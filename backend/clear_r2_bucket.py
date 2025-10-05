import os
import boto3
from botocore.client import Config
from dotenv import load_dotenv

load_dotenv()

def clear_r2_bucket():
    """Clear all objects from the R2 bucket"""
    account_id = os.getenv("R2_ACCOUNT_ID")
    access_key = os.getenv("R2_ACCESS_KEY_ID")
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
    bucket_name = os.getenv("R2_BUCKET_NAME")

    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4")
    )

    try:
        # List all objects in the bucket
        response = s3.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' in response:
            objects = response['Contents']
            print(f"Found {len(objects)} objects in bucket '{bucket_name}':")
            
            # Delete each object
            for obj in objects:
                key = obj['Key']
                s3.delete_object(Bucket=bucket_name, Key=key)
                print(f"Deleted: {key}")
            
            print(f"\n✅ Successfully cleared {len(objects)} objects from bucket '{bucket_name}'")
        else:
            print(f"✅ Bucket '{bucket_name}' is already empty")
            
    except Exception as e:
        print(f"❌ Error clearing bucket: {e}")

if __name__ == "__main__":
    clear_r2_bucket()



