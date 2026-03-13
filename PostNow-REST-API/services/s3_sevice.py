import logging
import os
import uuid

import boto3
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self):
        self.region = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
        self.client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=self.region
        )
        self.image_bucket = os.getenv('AWS_S3_IMAGE_BUCKET')

    def upload_image(self, user: User, image_bytes: bytes | str) -> str:
        """Upload a file to an S3 bucket"""
        try:
            unique_id = str(uuid.uuid4())
            user_prefix = f"user_{user.id}_" if user else ""
            filename = f"{user_prefix}generated_image_{unique_id}.png"
            self.client.put_object(
                Bucket=self.image_bucket,
                Key=filename,
                Body=image_bytes,
                ContentType='image/png',
            )

            image_url = f"https://{self.image_bucket}.s3.{self.region}.amazonaws.com/{filename}"
            logger.info(f"Image uploaded to S3: {image_url}")
            return image_url
        except Exception as e:
            logger.error(f"Error uploading file to S3: {e}")
            raise Exception(f"Failed to upload image to S3: {e}")

    def delete_image(self, image_key: str) -> None:
        """Delete a file from an S3 bucket"""
        try:
            self.client.delete_object(Bucket=self.image_bucket, Key=image_key)
        except Exception as e:
            logger.error(f"Error deleting file from S3: {e}")
            raise Exception(f"Failed to delete image from S3: {e}")

    def download_image(self, image_key: str) -> bytes:
        """Download a file from an S3 bucket"""
        try:
            response = self.client.get_object(
                Bucket=self.image_bucket, Key=image_key)
            return response['Body'].read()
        except Exception as e:
            logger.error(f"Error downloading file from S3: {e}")
            raise Exception(f"Failed to download image from S3: {e}")
