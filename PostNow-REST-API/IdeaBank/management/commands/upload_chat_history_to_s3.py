import os

import boto3
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from IdeaBank.models import ChatHistory


class Command(BaseCommand):
    help = 'Upload all chat history texts to S3 bucket without deleting from database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without uploading',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Process only the specified user ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        user_id = options['user_id']

        if dry_run:
            self.stdout.write(self.style.WARNING(
                'DRY RUN MODE - No uploads will be made'))

        # AWS S3 setup
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_S3_REGION_NAME')
        )
        bucket_name = os.getenv('AWS_S3_CHAT_HISTORY_BUCKET')

        if not bucket_name:
            self.stdout.write(self.style.ERROR(
                'AWS_S3_CHAT_HISTORY_BUCKET not set'))
            return

        # Get users
        if user_id:
            try:
                users = [User.objects.get(id=user_id)]
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'User with ID {user_id} does not exist'))
                return
        else:
            users = User.objects.filter(chathistory__isnull=False).distinct()

        total_users = len(users)
        self.stdout.write(f'Processing {total_users} users')

        uploaded_count = 0
        error_count = 0

        for user in users:
            try:
                # Get all chat history for user
                user_histories = ChatHistory.objects.filter(user=user)
                if not user_histories.exists():
                    continue

                # Aggregate history into text
                history_text = f"Chat History for User: {user.username} (ID: {user.id})\n\n"
                for chat_history in user_histories:
                    history_data = chat_history.get_history()
                    if history_data:
                        for item in history_data:
                            if isinstance(item, dict):
                                role = item.get('role', 'unknown')
                                content = item.get('content', '')
                                timestamp = item.get('timestamp', 'N/A')
                                history_text += f"[{timestamp}] {role}: {content}\n"
                        history_text += "\n--- End of Conversation ---\n\n"

                # File name
                file_name = f"chat_history_{user.id}.txt"

                if dry_run:
                    self.stdout.write(
                        f'Would upload {len(history_text)} chars for user: {user.username} as {file_name}')
                    uploaded_count += 1
                    continue

                # Upload to S3
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=file_name,
                    Body=history_text.encode('utf-8'),
                    ContentType='text/plain'
                )

                self.stdout.write(self.style.SUCCESS(
                    f'Uploaded chat history for user: {user.username}'))
                uploaded_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(
                    f'Error for user {user.username}: {str(e)}'))

        summary_msg = f'Upload completed. Uploaded: {uploaded_count}, Errors: {error_count}'
        if error_count > 0:
            self.stdout.write(self.style.ERROR(summary_msg))
        else:
            self.stdout.write(self.style.SUCCESS(summary_msg))
