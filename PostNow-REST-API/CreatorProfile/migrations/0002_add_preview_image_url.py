# Generated migration for adding preview_image_url to VisualStylePreference

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Adiciona campo preview_image_url ao modelo VisualStylePreference.
    Este campo armazena a URL da imagem de preview gerada para cada estilo visual.
    """

    dependencies = [
        ('CreatorProfile', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='visualstylepreference',
            name='preview_image_url',
            field=models.URLField(
                max_length=2000,
                blank=True,
                null=True,
                help_text='URL da imagem de preview do estilo visual no S3'
            ),
        ),
    ]
