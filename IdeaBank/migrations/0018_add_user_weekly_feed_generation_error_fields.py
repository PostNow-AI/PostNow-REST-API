# Generated manually for daily_generation_error fields on User model

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('IdeaBank', '0017_add_user_daily_generation_error_fields'),  # Latest IdeaBank migration
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE auth_user ADD COLUMN weekly_feed_generation_error TEXT NULL;",
            reverse_sql="ALTER TABLE auth_user DROP COLUMN weekly_feed_generation_error;"
        ),
    ]
