from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from IdeaBank.models import ChatHistory


class Command(BaseCommand):
    help = 'Aggregate all chat history entries per user into single entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making any changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING(
                'DRY RUN MODE - No changes will be made'))

        self.stdout.write('Starting chat history aggregation...')

        # Get all users who have chat history
        users_with_history = User.objects.filter(
            chathistory__isnull=False).distinct()

        total_users = users_with_history.count()
        self.stdout.write(f'Found {total_users} users with chat history')

        aggregated_count = 0
        error_count = 0
        skipped_count = 0

        for user in users_with_history:
            try:
                # Get all chat history entries for this user
                user_histories = ChatHistory.objects.filter(user=user)

                if user_histories.count() <= 1:
                    skipped_count += 1
                    continue  # Already aggregated or no history

                old_count = user_histories.count()
                self.stdout.write(
                    f'Processing user: {user.username} ({old_count} conversations)')

                # Aggregate all history data
                aggregated_history = []

                for chat_history in user_histories:
                    history_data = chat_history.get_history()
                    if history_data:
                        # Add conversation_id as metadata to each interaction if it exists
                        if hasattr(chat_history, 'conversation_id') and chat_history.conversation_id:
                            # Tag each interaction with its conversation_id
                            for item in history_data:
                                if isinstance(item, dict):
                                    item['_conversation_id'] = chat_history.conversation_id
                        aggregated_history.extend(history_data)

                # Sort by timestamp if available (assuming items have timestamps)
                try:
                    aggregated_history.sort(key=lambda x: x.get(
                        'timestamp', 0) if isinstance(x, dict) else 0)
                except Exception:
                    pass  # If sorting fails, keep original order

                if dry_run:
                    self.stdout.write(
                        f'  Would aggregate {len(aggregated_history)} interactions for user: {user.username}')
                    aggregated_count += 1
                    continue

                # Use transaction to ensure atomicity
                with transaction.atomic():
                    # FIRST: Create new aggregated entry
                    new_chat_history = ChatHistory.objects.create(user=user)
                    new_chat_history.set_history(aggregated_history)
                    new_chat_history.save()

                    # Verify the new entry was created and data is accessible
                    verification_data = new_chat_history.get_history()
                    if len(verification_data) != len(aggregated_history):
                        raise ValueError(
                            f'Data verification failed: expected {len(aggregated_history)} items, got {len(verification_data)}')

                    # SECOND: Only delete old entries after confirming new one is good
                    deleted_count, _ = user_histories.delete()

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  Successfully aggregated {len(aggregated_history)} interactions '
                            f'from {deleted_count} conversations for user: {user.username}'
                        )
                    )

                aggregated_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Error aggregating history for user {user.username}: {str(e)}')
                )
                # In case of error, the transaction will rollback automatically

        summary_msg = 'Chat history aggregation completed. '
        if dry_run:
            summary_msg += f'Would aggregate: {aggregated_count}, Skipped: {skipped_count}'
        else:
            summary_msg += f'Aggregated: {aggregated_count}, Errors: {error_count}, Skipped: {skipped_count}'

        if error_count > 0:
            self.stdout.write(self.style.ERROR(summary_msg))
        else:
            self.stdout.write(self.style.SUCCESS(summary_msg))
