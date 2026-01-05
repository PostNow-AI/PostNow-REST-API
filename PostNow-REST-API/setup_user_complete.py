import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sonora_REST_API.settings')
os.environ["USE_SQLITE"] = "True"
django.setup()

from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
from CreditSystem.models import UserCredits, SubscriptionPlan, UserSubscription
from CreatorProfile.models import CreatorProfile
from ClientContext.models import ClientContext
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal

User = get_user_model()
email = 'rogeriofr86@gmail.com'
password = 'admin123'

print("🚀 Iniciando configuração completa do usuário...")

# 1. Criar superusuário
if not User.objects.filter(email=email).exists():
    user = User.objects.create_user(email=email, password=password)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"✅ 1. Superusuário criado!")
else:
    user = User.objects.get(email=email)
    print(f"✅ 1. Superusuário já existe")

# 2. Verificar email
email_address, created = EmailAddress.objects.get_or_create(
    user=user,
    email=email,
    defaults={'verified': True, 'primary': True}
)
if not created:
    email_address.verified = True
    email_address.primary = True
    email_address.save()
print("✅ 2. E-mail verificado")

# 3. Adicionar créditos
user_credits, created = UserCredits.objects.get_or_create(
    user=user,
    defaults={
        'balance': Decimal('10000.00'),
        'monthly_credits_allocated': Decimal('10000.00')
    }
)
if not created:
    user_credits.balance = Decimal('10000.00')
    user_credits.monthly_credits_allocated = Decimal('10000.00')
    user_credits.save()
print(f"✅ 3. Créditos adicionados: {user_credits.balance}")

# 4. Criar plano e assinatura
plan, created = SubscriptionPlan.objects.get_or_create(
    name='Plano Pro (Teste)',
    defaults={
        'description': 'Plano de teste para desenvolvimento',
        'benefits': ["Acesso total", "10000 créditos mensais"],
        'interval': 'monthly',
        'price': Decimal('0.00'),
        'monthly_credits': Decimal('10000.00'),
        'is_active': True
    }
)
end_date = timezone.now() + timedelta(days=30)
subscription, created = UserSubscription.objects.get_or_create(
    user=user,
    defaults={
        'plan': plan,
        'start_date': timezone.now(),
        'end_date': end_date,
        'status': 'active'
    }
)
if not created:
    subscription.plan = plan
    subscription.end_date = end_date
    subscription.status = 'active'
    subscription.save()
print(f"✅ 4. Assinatura criada: {subscription.plan.name}")

# 5. Completar onboarding
profile, created = CreatorProfile.objects.get_or_create(user=user)
profile.onboarding_completed = True
profile.onboarding_completed_at = timezone.now()
profile.step_1_completed = True
profile.step_2_completed = True
profile.business_name = "Lancei Essa"
profile.business_description = "Plataforma de IA para criação de conteúdo"
profile.voice_tone = "professional"
profile.specialization = "Marketing Digital"
profile.visual_style_ids = [6, 7, 8]  # Primeiros 3 estilos
profile.save()
print(f"✅ 5. Perfil configurado com estilos: {profile.visual_style_ids}")

# 6. ClientContext
client_context, created = ClientContext.objects.get_or_create(user=user)
client_context.market_panorama = "Mercado de SaaS em crescimento"
client_context.target_audience_profile = "Empreendedores e pequenas empresas"
client_context.save()
print("✅ 6. ClientContext configurado")

print("\n" + "="*60)
print("🎉 CONFIGURAÇÃO COMPLETA!")
print("="*60)
print(f"📧 Email: {email}")
print(f"🔑 Senha: {password}")
print(f"💰 Créditos: {user_credits.balance}")
print(f"📅 Assinatura: {subscription.plan.name} (válida até {subscription.end_date.strftime('%d/%m/%Y')})")
print(f"🎨 Estilos visuais: {profile.visual_style_ids}")
print("\n🔄 AGORA: Faça login no sistema!")

