import os
import boto3
from botocore.client import Config
from dotenv import load_dotenv

load_dotenv()

def upload_to_r2_signed(file_path: str, expires_in: int = 600) -> str:
    """
    Uploads a file to Cloudflare R2 and returns a temporary signed URL.
    """
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

    file_key = os.path.basename(file_path)

    # Upload file to R2
    s3.upload_file(file_path, bucket_name, file_key)

    # Generate a temporary signed URL (default 10 minutes)
    signed_url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': file_key},
        ExpiresIn=expires_in
    )

    return signed_url
