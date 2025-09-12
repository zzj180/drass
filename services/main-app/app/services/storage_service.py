"""
Storage service abstraction for local and S3 storage
"""

import os
import logging
from typing import Optional, BinaryIO
from pathlib import Path
import aiofiles
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Abstract storage service supporting local and S3"""
    
    def __init__(self):
        self._initialized = False
        self.storage_type = getattr(settings, 'STORAGE_TYPE', 'local')
        self.storage_path = getattr(settings, 'STORAGE_PATH', './data/uploads')
        
        # S3 configuration
        self.s3_bucket = getattr(settings, 'S3_BUCKET', None)
        self.s3_region = getattr(settings, 'S3_REGION', 'us-east-1')
        self.s3_access_key = getattr(settings, 'S3_ACCESS_KEY_ID', None)
        self.s3_secret_key = getattr(settings, 'S3_SECRET_ACCESS_KEY', None)
        self.s3_endpoint_url = getattr(settings, 'S3_ENDPOINT_URL', None)  # For MinIO
        
        self.s3_client = None
    
    async def initialize(self):
        """Initialize storage service"""
        if self._initialized:
            return
        
        if self.storage_type == 'local':
            # Create local storage directory
            Path(self.storage_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Local storage initialized at {self.storage_path}")
            
        elif self.storage_type in ['s3', 'minio']:
            # Initialize S3/MinIO client
            try:
                session = boto3.Session(
                    aws_access_key_id=self.s3_access_key,
                    aws_secret_access_key=self.s3_secret_key,
                    region_name=self.s3_region
                )
                
                self.s3_client = session.client(
                    's3',
                    endpoint_url=self.s3_endpoint_url if self.storage_type == 'minio' else None
                )
                
                # Test connection by listing buckets
                self.s3_client.list_buckets()
                
                # Ensure bucket exists
                try:
                    self.s3_client.head_bucket(Bucket=self.s3_bucket)
                except ClientError:
                    # Create bucket if it doesn't exist
                    self.s3_client.create_bucket(
                        Bucket=self.s3_bucket,
                        CreateBucketConfiguration={'LocationConstraint': self.s3_region}
                        if self.s3_region != 'us-east-1' else {}
                    )
                    logger.info(f"Created S3 bucket: {self.s3_bucket}")
                
                logger.info(f"S3/MinIO storage initialized with bucket: {self.s3_bucket}")
                
            except Exception as e:
                logger.error(f"Failed to initialize S3/MinIO storage: {e}")
                raise
        
        self._initialized = True
    
    def _get_storage_path(self, user_id: str, file_id: str, file_extension: str) -> str:
        """Generate storage path for file"""
        # Organize by user and date
        from datetime import datetime
        date_path = datetime.utcnow().strftime("%Y/%m/%d")
        
        if self.storage_type == 'local':
            return os.path.join(
                self.storage_path,
                user_id,
                date_path,
                f"{file_id}{file_extension}"
            )
        else:
            # S3 key format
            return f"{user_id}/{date_path}/{file_id}{file_extension}"
    
    async def store_file(
        self,
        file_content: bytes,
        file_id: str,
        file_extension: str,
        user_id: str,
        metadata: Optional[dict] = None
    ) -> str:
        """Store file and return storage path"""
        storage_path = self._get_storage_path(user_id, file_id, file_extension)
        
        if self.storage_type == 'local':
            # Store locally
            full_path = Path(storage_path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(full_path, 'wb') as f:
                await f.write(file_content)
            
            logger.debug(f"Stored file locally: {storage_path}")
            
        elif self.storage_type in ['s3', 'minio']:
            # Store in S3/MinIO
            try:
                extra_args = {}
                if metadata:
                    extra_args['Metadata'] = metadata
                
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=storage_path,
                    Body=file_content,
                    **extra_args
                )
                
                logger.debug(f"Stored file in S3: {storage_path}")
                
            except Exception as e:
                logger.error(f"Failed to store file in S3: {e}")
                raise
        
        return storage_path
    
    async def get_file(self, storage_path: str) -> bytes:
        """Retrieve file content"""
        if self.storage_type == 'local':
            # Read from local storage
            async with aiofiles.open(storage_path, 'rb') as f:
                content = await f.read()
            return content
            
        elif self.storage_type in ['s3', 'minio']:
            # Retrieve from S3/MinIO
            try:
                response = self.s3_client.get_object(
                    Bucket=self.s3_bucket,
                    Key=storage_path
                )
                return response['Body'].read()
                
            except Exception as e:
                logger.error(f"Failed to retrieve file from S3: {e}")
                raise
    
    async def delete_file(self, storage_path: str) -> bool:
        """Delete file from storage"""
        try:
            if self.storage_type == 'local':
                # Delete from local storage
                if os.path.exists(storage_path):
                    os.remove(storage_path)
                    
                    # Try to remove empty parent directories
                    parent = Path(storage_path).parent
                    while parent != Path(self.storage_path):
                        try:
                            if not any(parent.iterdir()):
                                parent.rmdir()
                            parent = parent.parent
                        except:
                            break
                    
                    logger.debug(f"Deleted file locally: {storage_path}")
                    return True
                    
            elif self.storage_type in ['s3', 'minio']:
                # Delete from S3/MinIO
                self.s3_client.delete_object(
                    Bucket=self.s3_bucket,
                    Key=storage_path
                )
                logger.debug(f"Deleted file from S3: {storage_path}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
        
        return False
    
    async def file_exists(self, storage_path: str) -> bool:
        """Check if file exists"""
        if self.storage_type == 'local':
            return os.path.exists(storage_path)
            
        elif self.storage_type in ['s3', 'minio']:
            try:
                self.s3_client.head_object(
                    Bucket=self.s3_bucket,
                    Key=storage_path
                )
                return True
            except ClientError:
                return False
    
    async def get_file_size(self, storage_path: str) -> Optional[int]:
        """Get file size in bytes"""
        if self.storage_type == 'local':
            if os.path.exists(storage_path):
                return os.path.getsize(storage_path)
                
        elif self.storage_type in ['s3', 'minio']:
            try:
                response = self.s3_client.head_object(
                    Bucket=self.s3_bucket,
                    Key=storage_path
                )
                return response['ContentLength']
            except ClientError:
                pass
        
        return None
    
    async def generate_presigned_url(
        self,
        storage_path: str,
        expiration: int = 3600
    ) -> Optional[str]:
        """Generate presigned URL for direct access (S3 only)"""
        if self.storage_type in ['s3', 'minio']:
            try:
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.s3_bucket,
                        'Key': storage_path
                    },
                    ExpiresIn=expiration
                )
                return url
            except Exception as e:
                logger.error(f"Failed to generate presigned URL: {e}")
        
        return None
    
    async def list_files(
        self,
        prefix: str,
        max_items: int = 100
    ) -> list:
        """List files with given prefix"""
        files = []
        
        if self.storage_type == 'local':
            # List local files
            base_path = Path(self.storage_path) / prefix
            if base_path.exists():
                for file_path in base_path.rglob('*'):
                    if file_path.is_file():
                        files.append({
                            'path': str(file_path.relative_to(self.storage_path)),
                            'size': file_path.stat().st_size,
                            'modified': file_path.stat().st_mtime
                        })
                        if len(files) >= max_items:
                            break
                            
        elif self.storage_type in ['s3', 'minio']:
            # List S3 objects
            try:
                paginator = self.s3_client.get_paginator('list_objects_v2')
                page_iterator = paginator.paginate(
                    Bucket=self.s3_bucket,
                    Prefix=prefix,
                    PaginationConfig={'MaxItems': max_items}
                )
                
                for page in page_iterator:
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            files.append({
                                'path': obj['Key'],
                                'size': obj['Size'],
                                'modified': obj['LastModified'].timestamp()
                            })
                            
            except Exception as e:
                logger.error(f"Failed to list files from S3: {e}")
        
        return files
    
    async def close(self):
        """Clean up storage service"""
        self._initialized = False
        if self.s3_client:
            # boto3 client doesn't need explicit closing
            self.s3_client = None


# Singleton instance
storage_service = StorageService()