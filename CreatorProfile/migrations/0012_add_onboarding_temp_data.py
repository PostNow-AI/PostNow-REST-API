# Generated manually for OnboardingTempData model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CreatorProfile', '0011_alter_creatorprofile_business_phone'),
    ]

    operations = [
        migrations.CreateModel(
            name='OnboardingTempData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.CharField(
                    db_index=True,
                    help_text='Identificador único da sessão de onboarding',
                    max_length=100,
                    unique=True,
                    verbose_name='ID da Sessão'
                )),
                ('business_data', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='business_name, specialization, business_description, etc.',
                    verbose_name='Dados do Negócio'
                )),
                ('branding_data', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='voice_tone, colors, visual_style_ids, logo, etc.',
                    verbose_name='Dados de Marca'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateTimeField(
                    help_text='Data de expiração dos dados temporários (7 dias após criação)',
                    verbose_name='Expira em'
                )),
            ],
            options={
                'verbose_name': 'Dados Temporários de Onboarding',
                'verbose_name_plural': 'Dados Temporários de Onboarding',
            },
        ),
        migrations.AddIndex(
            model_name='onboardingtempdata',
            index=models.Index(fields=['expires_at'], name='CreatorProf_expires_b4f1e4_idx'),
        ),
    ]
