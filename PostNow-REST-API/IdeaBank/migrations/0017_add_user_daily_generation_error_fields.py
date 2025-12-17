# Generated manually for daily_generation_error fields on User model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('IdeaBank', '0016_delete_chathistory'),  # Latest IdeaBank migration
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE auth_user ADD COLUMN daily_generation_error TEXT NULL;",
            reverse_sql="ALTER TABLE auth_user DROP COLUMN daily_generation_error;"
        ),
        migrations.RunSQL(
            "ALTER TABLE auth_user ADD COLUMN daily_generation_error_date DATETIME NULL;",
            reverse_sql="ALTER TABLE auth_user DROP COLUMN daily_generation_error_date;"
        ),
    ]
