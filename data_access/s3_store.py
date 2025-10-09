"""
Amazon S3 Storage Interface for Trending Intelligence System
Handles JSON persistence, snapshots, and report storage with encryption and retries

Author: AI Assistant
Date: October 8, 2025
"""

import json
import gzip
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from io import BytesIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class S3Store:
    """
    S3 storage interface with encryption, retries, and atomic operations
    """

    def __init__(self):
        """Initialize S3 client with configuration"""
        self._client = None
        self.bucket = os.getenv('AWS_S3_BUCKET', '')
        self.prefix = os.getenv('AWS_S3_PREFIX', '')
        self.region = os.getenv('AWS_REGION', 'ap-southeast-2')
        self.kms_key_id = os.getenv('AWS_S3_KMS_KEY_ID', '')
        self.sse = os.getenv('AWS_S3_SSE', 'aws:kms' if self.kms_key_id else 'AES256')
        self.max_retries = int(os.getenv('AWS_MAX_RETRIES', '3'))
        self.timeout = int(os.getenv('AWS_TIMEOUT_SECONDS', '20'))
        
        if not self.bucket:
            logger.warning("[WARNING] AWS_S3_BUCKET not configured - S3 operations will fail")

    def get_s3_client(self) -> boto3.client:
        """Get or create S3 client with proper configuration"""
        if self._client is None:
            try:
                config = Config(
                    retries={'max_attempts': self.max_retries, 'mode': 'adaptive'},
                    read_timeout=self.timeout,
                    connect_timeout=self.timeout,
                    region_name=self.region,
                    max_pool_connections=50
                )
                
                self._client = boto3.client('s3', config=config)
                
                # Test credentials and bucket access
                self._client.head_bucket(Bucket=self.bucket)
                logger.info(f"[OK] S3 client initialized for bucket: {self.bucket}")
                
            except NoCredentialsError:
                logger.error("[ERROR] AWS credentials not found. Configure IAM role or credentials.")
                raise
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    logger.error(f"[ERROR] S3 bucket not found: {self.bucket}")
                else:
                    logger.error(f"[ERROR] S3 bucket access failed: {e}")
                raise
            except Exception as e:
                logger.error(f"[ERROR] Failed to initialize S3 client: {e}")
                raise
                
        return self._client

    def build_key(self, *parts: str) -> str:
        """
        Build S3 key from parts with proper prefix handling
        
        Args:
            *parts: Path components to join
            
        Returns:
            Complete S3 key with prefix applied
        """
        # Remove empty parts and join with "/"
        clean_parts = [part.strip('/') for part in parts if part.strip('/')]
        
        if self.prefix:
            # Ensure prefix doesn't start with "/"
            prefix_clean = self.prefix.strip('/')
            key = f"{prefix_clean}/" + "/".join(clean_parts)
        else:
            key = "/".join(clean_parts)
            
        # Ensure no leading slash for S3
        return key.lstrip('/')

    def s3_write_json(
        self, 
        key: str, 
        data: Union[Dict, List], 
        *, 
        compress: bool = False,
        content_type: str = "application/json"
    ) -> Dict:
        """
        Write JSON data to S3 with encryption and atomic operation
        
        Args:
            key: S3 key for the object
            data: JSON-serializable data to write
            compress: Whether to gzip compress the data
            content_type: Content-Type header
            
        Returns:
            Response dictionary with success status and metadata
        """
        try:
            client = self.get_s3_client()
            
            # Serialize JSON data
            json_data = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            
            # Prepare upload arguments
            put_args = {
                'Bucket': self.bucket,
                'Key': key,
                'ContentType': content_type,
                'Metadata': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'trending-intelligence',
                    'compressed': str(compress).lower()
                }
            }
            
            # Handle compression
            if compress:
                # Compress data
                buffer = BytesIO()
                with gzip.GzipFile(fileobj=buffer, mode='wb') as gz:
                    gz.write(json_data.encode('utf-8'))
                
                put_args['Body'] = buffer.getvalue()
                put_args['ContentEncoding'] = 'gzip'
            else:
                put_args['Body'] = json_data.encode('utf-8')
            
            # Configure server-side encryption
            if self.sse == 'aws:kms' and self.kms_key_id:
                put_args['ServerSideEncryption'] = 'aws:kms'
                put_args['SSEKMSKeyId'] = self.kms_key_id
            else:
                put_args['ServerSideEncryption'] = 'AES256'
            
            # Atomic write with retry logic
            response = self._retry_operation(
                lambda: client.put_object(**put_args),
                operation_name=f"s3_write_json({key})"
            )
            
            logger.info(f"[OK] S3 write successful: s3://{self.bucket}/{key}")
            
            return {
                'success': True,
                'key': key,
                'bucket': self.bucket,
                's3_url': f"s3://{self.bucket}/{key}",
                'size_bytes': len(put_args['Body']),
                'compressed': compress,
                'etag': response.get('ETag', '').strip('"'),
                'version_id': response.get('VersionId'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[ERROR] S3 write failed for key {key}: {e}")
            return {
                'success': False,
                'error': str(e),
                'key': key,
                'timestamp': datetime.utcnow().isoformat()
            }

    def s3_read_json(self, key: str) -> Optional[Union[Dict, List]]:
        """
        Read JSON data from S3 with automatic decompression
        
        Args:
            key: S3 key for the object
            
        Returns:
            Deserialized JSON data or None if not found
        """
        try:
            client = self.get_s3_client()
            
            # Get object with retry logic
            response = self._retry_operation(
                lambda: client.get_object(Bucket=self.bucket, Key=key),
                operation_name=f"s3_read_json({key})"
            )
            
            # Read body
            body = response['Body'].read()
            
            # Handle decompression if needed
            content_encoding = response.get('ContentEncoding', '')
            if content_encoding == 'gzip':
                body = gzip.decompress(body)
            
            # Decode and parse JSON
            json_str = body.decode('utf-8')
            data = json.loads(json_str)
            
            logger.debug(f"[OK] S3 read successful: s3://{self.bucket}/{key}")
            return data
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.debug(f"[NOT_FOUND] S3 object not found: s3://{self.bucket}/{key}")
                return None
            else:
                logger.error(f"[ERROR] S3 read failed for key {key}: {e}")
                return None
        except Exception as e:
            logger.error(f"[ERROR] S3 read failed for key {key}: {e}")
            return None

    def s3_exists(self, key: str) -> bool:
        """
        Check if S3 object exists
        
        Args:
            key: S3 key to check
            
        Returns:
            True if object exists, False otherwise
        """
        try:
            client = self.get_s3_client()
            
            self._retry_operation(
                lambda: client.head_object(Bucket=self.bucket, Key=key),
                operation_name=f"s3_exists({key})"
            )
            
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"[ERROR] S3 exists check failed for key {key}: {e}")
                return False
        except Exception as e:
            logger.error(f"[ERROR] S3 exists check failed for key {key}: {e}")
            return False

    def s3_list_prefix(self, prefix: str, max_keys: int = 1000) -> List[str]:
        """
        List objects under S3 prefix with pagination
        
        Args:
            prefix: S3 prefix to list
            max_keys: Maximum number of keys to return
            
        Returns:
            List of S3 keys matching the prefix
        """
        try:
            client = self.get_s3_client()
            keys = []
            
            # Build full prefix with bucket prefix
            full_prefix = self.build_key(prefix)
            
            paginator = client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket,
                Prefix=full_prefix,
                PaginationConfig={'MaxItems': max_keys}
            )
            
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        keys.append(obj['Key'])
            
            logger.debug(f"[OK] S3 list found {len(keys)} objects under prefix: {full_prefix}")
            return keys
            
        except Exception as e:
            logger.error(f"[ERROR] S3 list failed for prefix {prefix}: {e}")
            return []

    def get_presigned_url(self, key: str, expires_in: int = 3600, method: str = 'get_object') -> Optional[str]:
        """
        Generate presigned URL for S3 object
        
        Args:
            key: S3 key for the object
            expires_in: URL expiration time in seconds
            method: S3 method ('get_object' or 'put_object')
            
        Returns:
            Presigned URL or None if failed
        """
        try:
            client = self.get_s3_client()
            
            url = client.generate_presigned_url(
                method,
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            
            logger.debug(f"[OK] Generated presigned URL for: s3://{self.bucket}/{key}")
            return url
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to generate presigned URL for key {key}: {e}")
            return None

    def _retry_operation(self, operation, operation_name: str = "S3 operation"):
        """
        Execute S3 operation with exponential backoff retry logic
        
        Args:
            operation: Lambda function to execute
            operation_name: Name for logging
            
        Returns:
            Operation result
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return operation()
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                
                # Don't retry for client errors (4xx)
                if error_code in ['NoSuchBucket', 'NoSuchKey', 'AccessDenied', 'InvalidRequest']:
                    raise
                
                # Retry for server errors (5xx) and throttling
                if error_code in ['InternalError', 'ServiceUnavailable', 'SlowDown', 'RequestTimeout']:
                    last_exception = e
                    if attempt < self.max_retries:
                        delay = min(2 ** attempt, 10)  # Exponential backoff, max 10 seconds
                        logger.warning(f"[RETRY] {operation_name} attempt {attempt + 1} failed: {error_code}. Retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                
                # Don't retry for other errors
                raise
                
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = min(2 ** attempt, 10)
                    logger.warning(f"[RETRY] {operation_name} attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise
        
        # All retries exhausted
        logger.error(f"[ERROR] {operation_name} failed after {self.max_retries + 1} attempts")
        raise last_exception


# Global S3 store instance
_s3_store = None


def get_s3_store() -> S3Store:
    """Get or create global S3Store instance"""
    global _s3_store
    if _s3_store is None:
        _s3_store = S3Store()
    return _s3_store


# Convenience functions
def s3_write_json(key: str, data: Union[Dict, List], **kwargs) -> Dict:
    """Write JSON to S3 using global store instance"""
    return get_s3_store().s3_write_json(key, data, **kwargs)


def s3_read_json(key: str) -> Optional[Union[Dict, List]]:
    """Read JSON from S3 using global store instance"""
    return get_s3_store().s3_read_json(key)


def s3_exists(key: str) -> bool:
    """Check S3 object existence using global store instance"""
    return get_s3_store().s3_exists(key)


def s3_list_prefix(prefix: str, max_keys: int = 1000) -> List[str]:
    """List S3 objects by prefix using global store instance"""
    return get_s3_store().s3_list_prefix(prefix, max_keys)


def s3_delete_object(key: str) -> bool:
    """Delete S3 object using global store instance"""
    try:
        client = get_s3_store().get_s3_client()
        client.delete_object(Bucket=get_s3_store().bucket, Key=key)
        logger.info(f"[DELETE] S3 object deleted: {key}")
        return True
    except Exception as e:
        logger.error(f"[ERROR] S3 delete failed for key {key}: {e}")
        return False


def build_key(*parts: str) -> str:
    """Build S3 key using global store instance"""
    return get_s3_store().build_key(*parts)


if __name__ == "__main__":
    # Test S3 integration
    import sys
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test basic operations
    store = S3Store()
    
    print("Testing S3 Store Integration...")
    
    # Test key building
    key = store.build_key("test", "2025", "10", "test_file.json")
    print(f"Test key: {key}")
    
    # Test write/read roundtrip
    test_data = {
        "test": True,
        "timestamp": datetime.utcnow().isoformat(),
        "numbers": [1, 2, 3, 4, 5],
        "nested": {"level": 1, "data": "test"}
    }
    
    print("Writing test data...")
    result = store.s3_write_json(key, test_data)
    
    if result['success']:
        print(f"✅ Write successful: {result['s3_url']}")
        
        print("Reading test data...")
        read_data = store.s3_read_json(key)
        
        if read_data == test_data:
            print("✅ Read/write roundtrip successful!")
        else:
            print("❌ Data mismatch in roundtrip")
            sys.exit(1)
    else:
        print(f"❌ Write failed: {result['error']}")
        sys.exit(1)
    
    print("S3 Store test completed successfully!")