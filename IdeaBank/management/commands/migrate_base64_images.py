import base64
import os
import re
import uuid
from io import BytesIO

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from IdeaBank.models import PostIdea
from PIL import Image


class Command(BaseCommand):
    help = 'Migrate base64 images in PostIdea to S3 and update database URLs. Can filter by specific user.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of images to process at once (default: 10)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of images to process (for testing)',
        )
        parser.add_argument(
            '--user',
            type=int,
            help='Process images only for a specific user ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        limit = options['limit']
        user_id = options['user']

        # Get all PostIdea objects with base64 images
        base64_pattern = r'^data:image/(png|jpeg|jpg);base64,'
        queryset = PostIdea.objects.filter(image_url__regex=base64_pattern)

        # Filter by user if specified
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                queryset = queryset.filter(post__user=user)
                self.stdout.write(
                    f'Filtering images for user: {user.username} (ID: {user_id})'
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {user_id} does not exist.')
                )
                return

        if limit:
            queryset = queryset[:limit]

        total_count = queryset.count()

        if total_count == 0:
            if user_id:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'No base64 images found to migrate for user {user_id}.')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('No base64 images found to migrate.')
                )
            return

        if user_id:
            self.stdout.write(
                f'Found {total_count} PostIdea records with base64 images for user {user_id}.'
            )
        else:
            self.stdout.write(
                f'Found {total_count} PostIdea records with base64 images.'
            )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made.')
            )

        # Process in batches
        processed = 0
        successful = 0
        failed = 0

        for idea in queryset.iterator(chunk_size=batch_size):
            processed += 1

            try:
                new_url = self._migrate_image_to_s3(idea, dry_run)
                if new_url and not dry_run:
                    idea.image_url = new_url
                    idea.save(update_fields=['image_url'])
                    successful += 1
                elif new_url and dry_run:
                    successful += 1

                if processed % batch_size == 0:
                    self.stdout.write(
                        f'Processed {processed}/{total_count} images...')

            except Exception as e:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to migrate image for PostIdea {idea.id}: {str(e)}')
                )

        # Final summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('MIGRATION SUMMARY')
        self.stdout.write('='*50)
        self.stdout.write(f'Total images found: {total_count}')
        self.stdout.write(f'Successfully migrated: {successful}')
        self.stdout.write(f'Failed to migrate: {failed}')

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\nThis was a dry run. No changes were made to the database.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\nMigration completed!')
            )

    def _migrate_image_to_s3(self, idea, dry_run=False):
        """Migrate a single base64 image to S3."""
        image_url = idea.image_url

        if not image_url or not image_url.startswith('data:image/'):
            return None

        try:
            # Extract base64 data
            match = re.match(
                r'^data:image/(png|jpeg|jpg);base64,(.*)$', image_url)
            if not match:
                raise ValueError(
                    f"Invalid base64 image format: {image_url[:50]}...")

            image_format = match.group(1)
            base64_data = match.group(2)

            # Decode base64 to bytes
            try:
                image_bytes = base64.b64decode(base64_data)
            except Exception as e:
                raise ValueError(f"Failed to decode base64 data: {str(e)}")

            # Convert to proper format if needed
            image_bytes = self._process_image_bytes(image_bytes, image_format)

            if dry_run:
                # In dry run, just validate the image can be processed
                self.stdout.write(
                    f'[DRY RUN] Would migrate PostIdea {idea.id} ({len(image_bytes)} bytes)'
                )
                return f"s3://dry-run/{idea.id}.png"

            # Upload to S3
            s3_url = self._upload_to_s3(image_bytes, idea)
            return s3_url

        except Exception as e:
            raise Exception(f"Failed to process image: {str(e)}")

    def _process_image_bytes(self, image_bytes, original_format):
        """Process image bytes to ensure they're in a good format for S3."""
        try:
            # Try to open and re-save the image to ensure it's valid
            image = Image.open(BytesIO(image_bytes))

            # Convert to RGB if necessary (remove alpha channel)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()
                                     [-1])  # Use alpha as mask
                else:
                    background.paste(image)
                image = background

            # Save as PNG (good for lossless compression)
            buffer = BytesIO()
            image.save(buffer, format='PNG', optimize=True)
            return buffer.getvalue()

        except Exception:
            # If PIL processing fails, return original bytes
            return image_bytes

    def _upload_to_s3(self, image_bytes, idea):
        """Upload image bytes to S3 and return the public URL."""
        try:
            # Get S3 configuration
            image_bucket = os.getenv('AWS_S3_IMAGE_BUCKET')
            if not image_bucket:
                raise ValueError(
                    "AWS_S3_IMAGE_BUCKET environment variable not set")

            # Initialize S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
            )

            # Generate unique filename
            unique_id = str(uuid.uuid4())
            user_prefix = f"user_{idea.post.user.id}_" if idea.post.user else ""
            filename = f"{user_prefix}legacy_migrated_{unique_id}.png"

            # Upload to S3
            s3_client.put_object(
                Bucket=image_bucket,
                Key=filename,
                Body=image_bytes,
                ContentType='image/png',
                Metadata={
                    'original_post_idea_id': str(idea.id),
                    'user_id': str(idea.post.user.id) if idea.post.user else 'anonymous',
                    # Using UUID as timestamp
                    'migrated_at': str(uuid.uuid4()),
                    'post_type': idea.post.type if idea.post.type else 'unknown'
                }
            )

            # Generate public URL
            region = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
            image_url = f"https://{image_bucket}.s3.{region}.amazonaws.com/{filename}"

            self.stdout.write(
                f'✅ Migrated PostIdea {idea.id}: {len(image_bytes)} bytes → {image_url}'
            )

            return image_url

        except NoCredentialsError:
            raise Exception("AWS credentials not found")
        except ClientError as e:
            raise Exception(f"S3 upload error: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error uploading to S3: {e}")
