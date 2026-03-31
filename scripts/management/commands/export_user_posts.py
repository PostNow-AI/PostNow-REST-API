"""
Django management command to export posts from users with active subscriptions.

Creates individual Excel files and image archives per user, organized by email.

Directory structure:
    exports/
        user1@email.com/
            user1@email.com_posts.xlsx
            user1@email.com_images.zip
        user2@email.com/
            user2@email.com_posts.xlsx
            user2@email.com_images.zip
"""

import base64
import os
import re
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from openpyxl import Workbook

from CreditSystem.models import UserSubscriptionStatus
from IdeaBank.models import Post, PostIdea


class Command(BaseCommand):
    help = 'Export posts from users with active subscriptions to Excel and images to ZIP files'

    def __init__(self):
        super().__init__()
        self.stats = {
            'total_users': 0,
            'total_posts': 0,
            'total_images': 0,
            'failed_images': 0,
        }

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='exports',
            help='Output directory for exports (default: exports/)'
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        
        self.stdout.write(self.style.SUCCESS('Starting user post export...'))
        self.stdout.write(f'Output directory: {output_dir}/')
        
        # Query active users
        active_users = self.get_active_users()
        
        if not active_users:
            self.stdout.write(self.style.WARNING('No users with active subscriptions found.'))
            return
        
        self.stdout.write(f'Found {len(active_users)} users with active subscriptions')
        
        # Process each user
        for user in active_users:
            try:
                self.process_user(user, output_dir)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing user {user.email}: {str(e)}')
                )
                continue
        
        # Print summary
        self.print_summary()

    def get_active_users(self):
        """Query users with active subscriptions."""
        return User.objects.filter(
            subscription_status__has_active_subscription=True
        ).select_related('subscription_status')

    def process_user(self, user, output_dir):
        """Process a single user's posts and images."""
        self.stdout.write(f'\nProcessing user: {user.email}')
        
        # Get all posts for this user
        posts = Post.objects.filter(user=user).prefetch_related('ideas')
        
        if not posts.exists():
            self.stdout.write(self.style.WARNING(f'  No posts found for {user.email}'))
            return
        
        # Create user directory
        user_email_sanitized = self.sanitize_filename(user.email)
        user_dir = Path(output_dir) / user_email_sanitized
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Export to Excel
        excel_filename = f"{user_email_sanitized}_posts.xlsx"
        excel_path = user_dir / excel_filename
        post_count = self.export_to_excel(posts, excel_path)
        
        self.stdout.write(f'  ✓ Created Excel file: {excel_path}')
        self.stdout.write(f'    Posts exported: {post_count}')
        
        # Download and zip images
        image_count = self.export_images(posts, user_dir, user_email_sanitized)
        
        if image_count > 0:
            self.stdout.write(f'    Images exported: {image_count}')
        else:
            self.stdout.write(f'    No images found for this user')
        
        # Update stats
        self.stats['total_users'] += 1
        self.stats['total_posts'] += post_count
        self.stats['total_images'] += image_count

    def export_to_excel(self, posts, excel_path):
        """Export posts to Excel file."""
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Posts"
        
        # Write headers
        headers = ['Post Name', 'Content', 'Post Type']
        sheet.append(headers)
        
        # Make headers bold
        for cell in sheet[1]:
            cell.font = cell.font.copy(bold=True)
        
        # Write data
        post_count = 0
        for post in posts:
            # Get first PostIdea content if available
            first_idea = post.ideas.first()
            content = first_idea.content if first_idea else ''
            
            # Get post type display name
            post_type = post.get_type_display() if hasattr(post, 'get_type_display') else post.type
            
            row = [
                post.name or f'Post {post.id}',
                content,
                post_type
            ]
            sheet.append(row)
            post_count += 1
        
        # Adjust column widths
        sheet.column_dimensions['A'].width = 30
        sheet.column_dimensions['B'].width = 80
        sheet.column_dimensions['C'].width = 15
        
        # Save workbook
        workbook.save(excel_path)
        
        return post_count

    def export_images(self, posts, user_dir, user_email_sanitized):
        """Download/decode images and create zip archive."""
        temp_dir = tempfile.mkdtemp()
        image_count = 0
        
        try:
            # Process all posts and their ideas
            for post in posts:
                for idea in post.ideas.all():
                    if idea.image_url:
                        try:
                            filename = f"post_{post.id}_idea_{idea.id}"
                            image_path = self.download_or_decode_image(
                                idea.image_url,
                                temp_dir,
                                filename
                            )
                            if image_path:
                                image_count += 1
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'    Failed to download image for post {post.id}, idea {idea.id}: {str(e)}'
                                )
                            )
                            self.stats['failed_images'] += 1
            
            # Create zip file if images were downloaded
            if image_count > 0:
                zip_filename = f"{user_email_sanitized}_images.zip"
                zip_path = user_dir / zip_filename
                self.create_zip(temp_dir, zip_path)
                self.stdout.write(f'  ✓ Created ZIP file: {zip_path}')
        
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        return image_count

    def download_or_decode_image(self, image_url, output_dir, base_filename):
        """Download from URL or decode base64 image."""
        if not image_url:
            return None
        
        # Check if it's base64 data
        if image_url.startswith('data:image'):
            return self.decode_base64_image(image_url, output_dir, base_filename)
        else:
            return self.download_image_from_url(image_url, output_dir, base_filename)

    def decode_base64_image(self, data_url, output_dir, base_filename):
        """Decode base64 image data and save to file."""
        try:
            # Extract format and data
            # Format: data:image/png;base64,iVBORw0KG...
            match = re.match(r'data:image/(\w+);base64,(.+)', data_url)
            if not match:
                return None
            
            image_format = match.group(1)
            image_data = match.group(2)
            
            # Decode base64
            decoded_data = base64.b64decode(image_data)
            
            # Save to file
            filename = f"{base_filename}.{image_format}"
            file_path = Path(output_dir) / filename
            
            with open(file_path, 'wb') as f:
                f.write(decoded_data)
            
            return str(file_path)
        
        except Exception as e:
            raise Exception(f"Failed to decode base64 image: {str(e)}")

    def download_image_from_url(self, url, output_dir, base_filename):
        """Download image from external URL."""
        try:
            # Download with timeout
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Determine file extension from content-type or URL
            content_type = response.headers.get('content-type', '')
            if 'image/jpeg' in content_type or 'image/jpg' in content_type:
                ext = 'jpg'
            elif 'image/png' in content_type:
                ext = 'png'
            elif 'image/gif' in content_type:
                ext = 'gif'
            elif 'image/webp' in content_type:
                ext = 'webp'
            else:
                # Try to get extension from URL
                parsed_url = urlparse(url)
                path = parsed_url.path
                ext = path.split('.')[-1] if '.' in path else 'jpg'
            
            # Save to file
            filename = f"{base_filename}.{ext}"
            file_path = Path(output_dir) / filename
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return str(file_path)
        
        except Exception as e:
            raise Exception(f"Failed to download image from {url}: {str(e)}")

    def create_zip(self, source_dir, zip_path):
        """Create zip archive from directory."""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file  # Store files in root of zip
                    zipf.write(file_path, arcname=arcname)

    def sanitize_filename(self, filename):
        """Sanitize filename to be filesystem-safe."""
        # Replace invalid characters with underscore
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip('. ')
        return sanitized

    def print_summary(self):
        """Print export summary statistics."""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Export Summary:'))
        self.stdout.write('=' * 60)
        self.stdout.write(f"Total users processed:    {self.stats['total_users']}")
        self.stdout.write(f"Total posts exported:     {self.stats['total_posts']}")
        self.stdout.write(f"Total images exported:    {self.stats['total_images']}")
        
        if self.stats['failed_images'] > 0:
            self.stdout.write(
                self.style.WARNING(f"Failed image downloads:   {self.stats['failed_images']}")
            )
        
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('\n✓ Export completed successfully!'))
