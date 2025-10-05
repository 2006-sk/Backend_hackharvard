"""
Cloudflare R2 Integration Routes for ScamShield AI
Handles conversation data storage and retrieval
"""

import os
import json
import boto3
from fastapi import APIRouter, HTTPException, Depends
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

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
        logger.warning("⚠️ .env file not found")

# Load environment variables
load_env_file()

# Create router
router = APIRouter(prefix="/r2", tags=["R2 Storage"])

# R2 Configuration
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME', 'scamshield-data')

# Initialize R2 client
r2_client = None

def get_r2_client():
    """Get or create R2 client"""
    global r2_client
    if r2_client is None:
        try:
            r2_client = boto3.client(
                's3',
                endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
                aws_access_key_id=R2_ACCESS_KEY_ID,
                aws_secret_access_key=R2_SECRET_ACCESS_KEY
            )
            logger.info("✅ R2 Client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize R2 client: {e}")
            raise
    return r2_client

async def _update_full_transcript(client, convo_id: str):
    """Combine all transcript chunks into a full transcript"""
    try:
        # Get all transcript parts
        parts_response = client.list_objects_v2(
            Bucket=R2_BUCKET_NAME,
            Prefix=f"{convo_id}/transcript_updates/"
        )
        
        transcript_parts = []
        for obj in parts_response.get('Contents', []):
            part_response = client.get_object(Bucket=R2_BUCKET_NAME, Key=obj['Key'])
            part_data = json.loads(part_response['Body'].read().decode('utf-8'))
            transcript_parts.append(part_data)
        
        if not transcript_parts:
            logger.warning(f"No transcript parts found for {convo_id}")
            return
        
        # Sort by chunk_id to maintain order
        transcript_parts.sort(key=lambda x: x.get('chunk_id', ''))
        
        # Combine all transcript text
        full_transcript = " ".join([part.get('transcript', '') for part in transcript_parts])
        
        # Get metadata from the latest part
        latest_part = transcript_parts[-1]
        
        # Create full transcript object
        full_transcript_data = {
            "convo_id": convo_id,
            "transcript": full_transcript,
            "total_parts": len(transcript_parts),
            "created_at": latest_part.get('timestamp'),
            "updated_at": latest_part.get('timestamp'),
            "metadata": latest_part.get('metadata', {}),
            "parts_summary": [
                {
                    "chunk_id": part.get('chunk_id'),
                    "timestamp": part.get('timestamp'),
                    "length": len(part.get('transcript', ''))
                }
                for part in transcript_parts
            ]
        }
        
        # Upload full transcript
        full_key = f"{convo_id}/transcript_full.json"
        client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=full_key,
            Body=json.dumps(full_transcript_data, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"📝 Combined {len(transcript_parts)} chunks into full transcript: {full_key}")
        
    except Exception as e:
        logger.error(f"❌ Failed to update full transcript for {convo_id}: {e}")
        raise

async def check_r2_connection() -> Dict[str, Any]:
    """Check R2 connection and bucket existence"""
    try:
        client = get_r2_client()
        
        # Try to access the specific bucket directly
        try:
            response = client.head_bucket(Bucket=R2_BUCKET_NAME)
            logger.info(f"✅ R2 Connected - Bucket '{R2_BUCKET_NAME}' exists")
            bucket_exists = True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"⚠️ Bucket '{R2_BUCKET_NAME}' not found, creating...")
                try:
                    client.create_bucket(Bucket=R2_BUCKET_NAME)
                    logger.info(f"✅ Created bucket '{R2_BUCKET_NAME}'")
                    bucket_exists = True
                except ClientError as create_error:
                    logger.error(f"❌ Failed to create bucket: {create_error}")
                    return {
                        "status": "error",
                        "message": f"Failed to create bucket '{R2_BUCKET_NAME}'",
                        "error": str(create_error)
                    }
            else:
                logger.error(f"❌ Bucket access error: {e}")
                return {
                    "status": "error",
                    "message": f"Cannot access bucket '{R2_BUCKET_NAME}': {str(e)}",
                    "bucket": None
                }
        
        # Try to list objects in the bucket to verify access
        try:
            objects_response = client.list_objects_v2(Bucket=R2_BUCKET_NAME, MaxKeys=1)
            logger.info(f"✅ Can list objects in bucket '{R2_BUCKET_NAME}'")
        except ClientError as e:
            logger.warning(f"⚠️ Cannot list objects in bucket: {e}")
        
        return {
            "status": "ok",
            "bucket": R2_BUCKET_NAME,
            "bucket_exists": bucket_exists,
            "message": "R2 connection successful"
        }
        
    except NoCredentialsError:
        logger.error("❌ R2 credentials not found")
        return {
            "status": "error",
            "message": "R2 credentials not configured",
            "bucket": None
        }
    except Exception as e:
        logger.error(f"❌ R2 connection error: {e}")
        return {
            "status": "error",
            "message": f"R2 connection failed: {str(e)}",
            "bucket": None
        }

@router.get("/check")
async def check_r2():
    """Check R2 connection status"""
    return await check_r2_connection()

@router.post("/convo/{convo_id}")
async def upload_convo_chunk(convo_id: str, data: Dict[str, Any]):
    """Upload or update a conversation chunk"""
    try:
        client = get_r2_client()
        
        # Validate input
        if not data:
            raise HTTPException(status_code=400, detail="No data provided")
        
        chunk_id = data.get('chunk_id', 'part1')
        
        # Create the key path
        key = f"{convo_id}/transcript_updates/{chunk_id}.json"
        
        # Prepare the data to store
        chunk_data = {
            "convo_id": convo_id,
            "chunk_id": chunk_id,
            "timestamp": data.get('timestamp'),
            "transcript": data.get('data', ''),
            "metadata": data.get('metadata', {})
        }
        
        # Upload to R2
        client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=key,
            Body=json.dumps(chunk_data, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"📤 Uploaded chunk to R2: {key}")
        
        # Automatically combine all chunks into full transcript
        try:
            await _update_full_transcript(client, convo_id)
            logger.info(f"📝 Updated full transcript for {convo_id}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to update full transcript: {e}")
        
        return {
            "status": "ok",
            "convo_id": convo_id,
            "chunk_id": chunk_id,
            "key": key,
            "message": "Chunk uploaded and full transcript updated"
        }
        
    except Exception as e:
        logger.error(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/convo/{convo_id}")
async def get_convo(convo_id: str):
    """Get full conversation data (transcript, meta, risk)"""
    try:
        client = get_r2_client()
        
        # Initialize response structure
        convo_data = {
            "convo_id": convo_id,
            "transcript_full": "",
            "transcript_parts": [],
            "metadata": {},
            "risk_data": {},
            "status": "incomplete"
        }
        
        # Try to get meta.json
        try:
            meta_response = client.get_object(Bucket=R2_BUCKET_NAME, Key=f"{convo_id}/meta.json")
            meta_data = json.loads(meta_response['Body'].read().decode('utf-8'))
            convo_data["metadata"] = meta_data
            logger.info(f"📄 Loaded metadata for {convo_id}")
        except ClientError:
            logger.info(f"📄 No metadata found for {convo_id}")
        
        # Try to get risk.json
        try:
            risk_response = client.get_object(Bucket=R2_BUCKET_NAME, Key=f"{convo_id}/risk.json")
            risk_data = json.loads(risk_response['Body'].read().decode('utf-8'))
            convo_data["risk_data"] = risk_data
            logger.info(f"📊 Loaded risk data for {convo_id}")
        except ClientError:
            logger.info(f"📊 No risk data found for {convo_id}")
        
        # Try to get transcript_full.json
        try:
            transcript_response = client.get_object(Bucket=R2_BUCKET_NAME, Key=f"{convo_id}/transcript_full.json")
            transcript_data = json.loads(transcript_response['Body'].read().decode('utf-8'))
            convo_data["transcript_full"] = transcript_data.get('transcript', '')
            logger.info(f"📝 Loaded full transcript for {convo_id}")
        except ClientError:
            logger.info(f"📝 No full transcript found for {convo_id}")
        
        # Get all transcript parts
        try:
            parts_response = client.list_objects_v2(
                Bucket=R2_BUCKET_NAME,
                Prefix=f"{convo_id}/transcript_updates/"
            )
            
            transcript_parts = []
            for obj in parts_response.get('Contents', []):
                part_response = client.get_object(Bucket=R2_BUCKET_NAME, Key=obj['Key'])
                part_data = json.loads(part_response['Body'].read().decode('utf-8'))
                transcript_parts.append(part_data)
            
            # Sort by chunk_id
            transcript_parts.sort(key=lambda x: x.get('chunk_id', ''))
            convo_data["transcript_parts"] = transcript_parts
            
            # Combine all transcript parts
            if transcript_parts:
                combined_transcript = " ".join([part.get('transcript', '') for part in transcript_parts])
                convo_data["transcript_full"] = combined_transcript
                convo_data["status"] = "complete"
            
            logger.info(f"📝 Loaded {len(transcript_parts)} transcript parts for {convo_id}")
            
        except ClientError:
            logger.info(f"📝 No transcript parts found for {convo_id}")
        
        return {
            "status": "ok",
            "convo_id": convo_id,
            "data": convo_data
        }
        
    except Exception as e:
        logger.error(f"❌ Get convo error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")

@router.put("/convo/{convo_id}/risk")
async def update_risk_score(convo_id: str, risk_data: Dict[str, Any]):
    """Update risk score for a conversation"""
    try:
        client = get_r2_client()
        
        # Validate input
        if not risk_data:
            raise HTTPException(status_code=400, detail="No risk data provided")
        
        # Prepare the risk data
        risk_json = {
            "convo_id": convo_id,
            "risk_score": risk_data.get('risk_score'),
            "risk_band": risk_data.get('risk_band', 'UNKNOWN'),
            "prediction": risk_data.get('prediction', 'unknown'),
            "timestamp": risk_data.get('timestamp'),
            "analysis_details": risk_data.get('analysis_details', {}),
            "keywords_found": risk_data.get('keywords_found', [])
        }
        
        # Upload to R2
        key = f"{convo_id}/risk.json"
        client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=key,
            Body=json.dumps(risk_json, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"📊 Updated risk data in R2: {key}")
        
        return {
            "ok": True,
            "convo_id": convo_id,
            "risk_score": risk_data.get('risk_score'),
            "risk_band": risk_data.get('risk_band'),
            "key": key,
            "message": "Risk score updated successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Risk update error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update risk: {str(e)}")

@router.put("/convo/{convo_id}/meta")
async def update_metadata(convo_id: str, metadata: Dict[str, Any]):
    """Update conversation metadata"""
    try:
        client = get_r2_client()
        
        # Prepare the metadata
        meta_json = {
            "convo_id": convo_id,
            "created_at": metadata.get('created_at'),
            "updated_at": metadata.get('updated_at'),
            "call_duration": metadata.get('call_duration'),
            "stream_sid": metadata.get('stream_sid'),
            "phone_number": metadata.get('phone_number'),
            "call_type": metadata.get('call_type'),
            "status": metadata.get('status', 'active')
        }
        
        # Upload to R2
        key = f"{convo_id}/meta.json"
        client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=key,
            Body=json.dumps(meta_json, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"📄 Updated metadata in R2: {key}")
        
        return {
            "ok": True,
            "convo_id": convo_id,
            "key": key,
            "message": "Metadata updated successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Metadata update error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update metadata: {str(e)}")

@router.get("/convo/{convo_id}/list")
async def list_convo_objects(convo_id: str):
    """List all objects for a conversation"""
    try:
        client = get_r2_client()
        
        # List all objects with the conversation prefix
        response = client.list_objects_v2(
            Bucket=R2_BUCKET_NAME,
            Prefix=f"{convo_id}/"
        )
        
        objects = []
        for obj in response.get('Contents', []):
            objects.append({
                "key": obj['Key'],
                "size": obj['Size'],
                "last_modified": obj['LastModified'].isoformat()
            })
        
        return {
            "status": "ok",
            "convo_id": convo_id,
            "objects": objects,
            "total_objects": len(objects)
        }
        
    except Exception as e:
        logger.error(f"❌ List objects error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list objects: {str(e)}")

# Health check endpoint for R2
@router.post("/convo/{convo_id}/combine")
async def combine_transcript_chunks(convo_id: str):
    """Manually combine all transcript chunks into full transcript"""
    try:
        client = get_r2_client()
        await _update_full_transcript(client, convo_id)
        
        return {
            "status": "ok",
            "convo_id": convo_id,
            "message": "Transcript chunks combined successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Combine chunks error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to combine chunks: {str(e)}")

@router.get("/health")
async def r2_health():
    """R2 health check"""
    connection_status = await check_r2_connection()
    return {
        "service": "R2 Storage",
        "status": "healthy" if connection_status.get("status") == "ok" else "unhealthy",
        "details": connection_status
    }
