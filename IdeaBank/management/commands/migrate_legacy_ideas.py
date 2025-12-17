from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from IdeaBank.models import Campaign, CampaignIdea, IdeaGenerationConfig


class Command(BaseCommand):
    help = 'Migrate legacy ideas to new campaign structure'

    def handle(self, *args, **options):
        self.stdout.write('Starting migration of legacy ideas...')

        # Get the first available user
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('No users found in the system'))
            return

        self.stdout.write(f'Using user: {user.email}')

        # Get all legacy ideas
        legacy_ideas = CampaignIdea.objects.filter(campaign__isnull=True)
        self.stdout.write(
            f'Found {legacy_ideas.count()} legacy ideas to migrate')

        migrated_count = 0

        for idea in legacy_ideas:
            try:
                # Create a campaign for this idea
                campaign = Campaign.objects.create(
                    user=user,
                    title=f'Campanha Migrada - {idea.title}',
                    description=f'Campanha criada automaticamente durante migração para ideia: {idea.title}',
                    objectives=['engagement'],  # Default objective
                    platforms=[idea.platform],
                    content_types={idea.platform: [idea.content_type]},
                    voice_tone='professional',
                    status='draft'
                )

                # Update the idea to link to the campaign
                idea.campaign = campaign
                idea.save()

                migrated_count += 1
                self.stdout.write(f'Migrated idea: {idea.title}')

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to migrate idea {idea.title}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully migrated {migrated_count} ideas')
        )

        # Clean up legacy configs
        legacy_configs = IdeaGenerationConfig.objects.all()
        if legacy_configs.exists():
            self.stdout.write(
                f'Removing {legacy_configs.count()} legacy configs...')
            legacy_configs.delete()
            self.stdout.write('Legacy configs removed')

        self.stdout.write('Migration completed!')
