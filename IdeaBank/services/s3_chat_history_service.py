import base64
import json
import zlib
from typing import List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from django.conf import settings
from django.contrib.auth.models import User


class S3ChatHistoryService:
    """Service for managing chat history storage in AWS S3 bucket."""

    def __init__(self):
        """Initialize S3 client with AWS credentials."""
        self.bucket_name = getattr(
            settings, 'AWS_S3_CHAT_HISTORY_BUCKET', 'postnow-history-bucket')

        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=getattr(
                    settings, 'AWS_SECRET_ACCESS_KEY'),
                region_name=getattr(
                    settings, 'AWS_S3_REGION_NAME', 'us-east-1')
            )
            print("✅ S3 client initialized successfully")
        except NoCredentialsError:
            print("❌ AWS credentials not found. S3 chat history will not work.")
            self.s3_client = None
        except Exception as e:
            print(f"❌ Failed to initialize S3 client: {e}")
            self.s3_client = None

    def _get_file_key(self, user: User) -> str:
        """Generate S3 file key for user's chat history."""
        return f"chat_history_{user.id}.txt"

    def _encode_history_data(self, history_data: List[dict]) -> str:
        """Encode history data using zlib compression and base64 encoding (same as database)."""
        try:
            # Convert to JSON string
            json_str = json.dumps(
                history_data, ensure_ascii=False, separators=(',', ':'))
            # Compress using zlib with maximum compression
            compressed = zlib.compress(json_str.encode('utf-8'), level=9)
            # Encode to base64 for safe text storage
            encoded = base64.b64encode(compressed).decode('ascii')
            return encoded
        except Exception as e:
            print(f"Error encoding history data: {e}")
            return ""

    def _decode_history_data(self, encoded_data: str) -> List[dict]:
        """Decode history data from base64 and zlib compression."""
        try:
            if not encoded_data or encoded_data.strip() == "":
                return []

            # Decode from base64
            compressed = base64.b64decode(encoded_data.encode('ascii'))
            # Decompress
            json_str = zlib.decompress(compressed).decode('utf-8')
            # Parse JSON
            return json.loads(json_str)
        except Exception as e:
            print(f"Error decoding history data: {e}")
            return []

    def get_history(self, user: User) -> List[dict]:
        """Retrieve chat history from S3 bucket."""
        if not self.s3_client:
            print("❌ S3 client not available")
            return []

        file_key = self._get_file_key(user)

        try:
            # Try to get the object from S3
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=file_key)
            encoded_data = response['Body'].read().decode('utf-8')

            if encoded_data:
                history_data = self._decode_history_data(encoded_data)
                print(
                    f"📖 Retrieved {len(history_data)} chat history items from S3 for user {user.username}")
                return history_data
            else:
                print(
                    f"📭 No chat history found in S3 for user {user.username}")
                return []

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                # File doesn't exist yet, return empty history
                print(
                    f"📭 Chat history file not found in S3 for user {user.username} (this is normal for new users)")
                return []
            else:
                print(
                    f"❌ S3 error retrieving chat history for user {user.username}: {e}")
                return []
        except Exception as e:
            print(
                f"❌ Unexpected error retrieving chat history for user {user.username}: {e}")
            return []

    def save_history(self, user: User, history_data: List[dict]) -> bool:
        """Save chat history to S3 bucket."""
        if not self.s3_client:
            print("❌ S3 client not available")
            return False

        if not history_data:
            print(f"⚠️ No history data to save for user {user.username}")
            return True  # Not an error, just nothing to save

        file_key = self._get_file_key(user)
        encoded_data = self._encode_history_data(history_data)

        if not encoded_data:
            print(f"❌ Failed to encode history data for user {user.username}")
            return False

        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=encoded_data.encode('utf-8'),
                ContentType='text/plain',
                # Optional: Add metadata
                Metadata={
                    'user_id': str(user.id),
                    'username': user.username,
                    'item_count': str(len(history_data))
                }
            )

            print(
                f"💾 Successfully saved {len(history_data)} chat history items to S3 for user {user.username}")
            return True

        except ClientError as e:
            print(
                f"❌ S3 error saving chat history for user {user.username}: {e}")
            return False
        except Exception as e:
            print(
                f"❌ Unexpected error saving chat history for user {user.username}: {e}")
            return False

    def append_interaction(self, user: User, new_history_data: List[dict]) -> bool:
        """Save the complete chat history returned by Gemini to S3 (replaces existing history)."""
        if not new_history_data:
            print(f"⚠️ No history data to save for user {user.username}")
            return True  # Not an error, just nothing to save

        # Save the complete history directly (don't append to existing, just replace)
        return self.save_history(user, new_history_data)

    def delete_history(self, user: User) -> bool:
        """Delete chat history file from S3 bucket."""
        if not self.s3_client:
            print("❌ S3 client not available")
            return False

        file_key = self._get_file_key(user)

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            print(
                f"🗑️ Successfully deleted chat history from S3 for user {user.username}")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                print(
                    f"📭 Chat history file already doesn't exist in S3 for user {user.username}")
                return True  # Not an error
            else:
                print(
                    f"❌ S3 error deleting chat history for user {user.username}: {e}")
                return False
        except Exception as e:
            print(
                f"❌ Unexpected error deleting chat history for user {user.username}: {e}")
            return False

    def list_all_histories(self) -> List[str]:
        """List all chat history files in the bucket (for admin purposes)."""
        if not self.s3_client:
            print("❌ S3 client not available")
            return []

        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix='chat_history_')
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents']]
                print(f"📋 Found {len(files)} chat history files in S3")
                return files
            else:
                print("📭 No chat history files found in S3")
                return []
        except Exception as e:
            print(f"❌ Error listing chat history files: {e}")
            return []

    def get_history_stats(self, user: User) -> Optional[dict]:
        """Get statistics about user's chat history file."""
        if not self.s3_client:
            return None

        file_key = self._get_file_key(user)

        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name, Key=file_key)
            return {
                'size': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag', '').strip('"'),
                'metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            else:
                print(
                    f"❌ Error getting history stats for user {user.username}: {e}")
                return None
        except Exception as e:
            print(
                f"❌ Unexpected error getting history stats for user {user.username}: {e}")
            return None
