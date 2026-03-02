# Generated manually for enrichment fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ClientContext', '0003_alter_clientcontext_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientcontext',
            name='tendencies_data',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.AddField(
            model_name='clientcontext',
            name='context_enrichment_status',
            field=models.CharField(
                blank=True,
                choices=[('pending', 'Pending'), ('enriched', 'Enriched'), ('failed', 'Failed')],
                default='pending',
                max_length=20,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='clientcontext',
            name='context_enrichment_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='clientcontext',
            name='context_enrichment_error',
            field=models.TextField(blank=True, default='', null=True),
        ),
    ]
