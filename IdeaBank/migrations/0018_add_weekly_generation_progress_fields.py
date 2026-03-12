# Generated manually for weekly_generation_progress fields on User model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("IdeaBank", "0017_add_user_daily_generation_error_fields"),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE auth_user ADD COLUMN weekly_generation_progress INTEGER DEFAULT 0 NOT NULL;",
            reverse_sql="ALTER TABLE auth_user DROP COLUMN weekly_generation_progress;",
        ),
        migrations.RunSQL(
            "ALTER TABLE auth_user ADD COLUMN weekly_generation_week VARCHAR(10) NULL;",
            reverse_sql="ALTER TABLE auth_user DROP COLUMN weekly_generation_week;",
        ),
    ]
