#!/usr/bin/env python3
"""
Script para enviar o terceiro email da campanha de reativação.
Envia para usuários que receberam Email 2 e ainda não reativaram.

Assunto: O Plano Legado: um presente para quem começou com a gente
Timing: Dia 7 (7 dias após Email 1, 4 dias após Email 2)

Uso:
    python scripts/reactivation_email_3.py [--dry-run] [--user-id=<uuid>]
"""
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

import django
import stripe
from asgiref.sync import sync_to_async

# Adiciona o diretório raiz ao Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configura o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sonora_REST_API.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model

# Configura Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
from django.template.loader import render_to_string
from django.utils import timezone

from CreditSystem.models import UserSubscription, SubscriptionPlan
from OnboardingCampaign.models import ReactivationEmail
from services.mailjet_service import MailjetService

User = get_user_model()


async def get_target_users():
    """
    Retorna usuários elegíveis para o email 3 de reativação.
    
    Critérios:
    - Receberam Email 2
    - NÃO reativaram desde então
    - NÃO receberam Email 3 antes
    """
    cutoff_date = timezone.make_aware(datetime(2025, 12, 25, 23, 59, 59))

    # Usuários que receberam Email 2
    users_with_email_2 = await sync_to_async(lambda: ReactivationEmail.objects.filter(
        email_number=ReactivationEmail.EMAIL_2,
        sent_at__isnull=False
    ).values_list('user_id', flat=True))()

    # Usuários que reativaram após 25/12/2025
    users_who_reactivated = await sync_to_async(lambda: UserSubscription.objects.filter(
        status='active',
        start_date__gt=cutoff_date
    ).values_list('user_id', flat=True).distinct())()

    # Usuários que já receberam Email 3
    users_already_sent = await sync_to_async(lambda: ReactivationEmail.objects.filter(
        email_number=ReactivationEmail.EMAIL_3,
        sent_at__isnull=False
    ).values_list('user_id', flat=True))()

    # Filtra usuários elegíveis
    target_users = await sync_to_async(lambda: User.objects.filter(
        id__in=users_with_email_2
    ).exclude(
        id__in=users_who_reactivated
    ).exclude(
        id__in=users_already_sent
    ).filter(
        email__isnull=False
    ).exclude(
        email=''
    ))()

    return target_users


async def send_reactivation_email_3(user, dry_run=False):
    """
    Envia o terceiro email de reativação para um usuário.
    
    Args:
        user: Instância de User
        dry_run: Se True, apenas simula o envio
        
    Returns:
        tuple: (success, message)
    """
    try:
        # Verifica se já enviou Email 3
        existing = await sync_to_async(ReactivationEmail.objects.filter(
            user=user,
            email_number=ReactivationEmail.EMAIL_3
        ).first)()

        if existing and existing.sent_at:
            return False, f"Email 3 já enviado em {existing.sent_at}"

        # Busca o Plano Legado
        legacy_plan = await sync_to_async(SubscriptionPlan.objects.filter(interval='legacy').first)()
        if not legacy_plan:
            return False, "Plano Legado não encontrado. Execute create_legacy_plan.py primeiro"

        if not legacy_plan.stripe_price_id:
            return False, "Plano Legado não possui stripe_price_id configurado"

        # Cria sessão de checkout do Stripe
        frontend_url = os.getenv('FRONTEND_URL', 'https://postnow.app')

        checkout_session = await sync_to_async(stripe.checkout.Session.create)(
            customer_email=user.email,
            payment_method_types=['card'],
            line_items=[{
                'price': legacy_plan.stripe_price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f'{frontend_url}/subscription/success',
            cancel_url=f'{frontend_url}/subscription/cancel',
            metadata={
                'user_id': str(user.id),
                'plan_id': str(legacy_plan.id),
                'source': 'reactivation_email',
                'email_number': '3',
                'campaign': 'legacy_2026'
            },
            subscription_data={
                'metadata': {
                    'user_id': str(user.id),
                    'plan_id': str(legacy_plan.id),
                },
                'trial_period_days': 7
            },
        )

        # Prepara contexto do template
        context = {
            'user_name': user.first_name or user.username or 'Olá',
            'subscription_url': checkout_session.url,
            'current_year': datetime.now().year,
            'frontend_url': frontend_url,
            'legacy_price': str(legacy_plan.price)
        }

        # Renderiza template
        html_content = await sync_to_async(render_to_string)('reactivation/email_3.html', context)
        subject = "O Plano Legado: um presente para quem começou com a gente"

        if dry_run:
            print(f"   [DRY RUN] Enviaria email para: {user.email}")
            print(f"   Assunto: {subject}")
            return True, "Dry run - email não enviado"

        # Envia email
        mailjet_service = MailjetService()
        success, response = await mailjet_service.send_email(
            to_email=user.email,
            subject=subject,
            body=html_content
        )

        if success:
            # Registra envio
            if existing:
                existing.sent_at = timezone.now()
                await sync_to_async(existing.save)()
            else:
                await sync_to_async(ReactivationEmail.objects.create)(
                    user=user,
                    email_number=ReactivationEmail.EMAIL_3,
                    sent_at=timezone.now()
                )

            return True, f"Email enviado com sucesso para {user.email}"
        else:
            return False, f"Falha ao enviar email: {response}"

    except Exception as e:
        return False, f"Erro ao processar usuário {user.email}: {str(e)}"


async def main_async(dry_run=False, user_id=None):
    """Função principal assíncrona"""
    print("=" * 70)
    print("📧 CAMPANHA DE REATIVAÇÃO - EMAIL 3 (DIA 7 - FINAL)")
    print("Assunto: O Plano Legado: um presente para quem começou com a gente")
    print("=" * 70)

    if dry_run:
        print("\n🔍 MODO DRY RUN - Nenhum email será enviado\n")

    # Verifica se o Plano Legado existe
    legacy_plan = await sync_to_async(SubscriptionPlan.objects.filter(interval='legacy').first)()
    if not legacy_plan:
        print("\n❌ ERRO: Plano Legado não encontrado!")
        print("Execute primeiro: python scripts/create_legacy_plan.py")
        return

    print(f"✅ Plano Legado encontrado: R$ {legacy_plan.price}")

    # Filtra usuários
    if user_id:
        print(f"\n🎯 Enviando apenas para usuário: {user_id}")
        users = await sync_to_async(lambda: User.objects.filter(id=user_id))()
        exists = await sync_to_async(lambda: users.exists())()
        if not exists:
            print(f"❌ Usuário {user_id} não encontrado")
            return
    else:
        print("\n🔍 Buscando usuários elegíveis...")
        users = await get_target_users()

    total = await sync_to_async(lambda: users.count())()
    print(f"📊 Total de usuários elegíveis: {total}")

    if total == 0:
        print("\n✅ Nenhum usuário para processar")
        return

    # Confirma antes de enviar (se não for dry run)
    if not dry_run and not user_id:
        print(f"\n⚠️  Você está prestes a enviar {total} emails (ÚLTIMA RODADA DA CAMPANHA).")
        confirm = input("Digite 'SIM' para continuar: ")
        if confirm != 'SIM':
            print("❌ Operação cancelada")
            return

    # Envia emails
    print(f"\n📤 Enviando emails...\n")
    sent = 0
    failed = 0
    skipped = 0

    users_list = await sync_to_async(lambda: list(users))()
    for user in users_list:
        success, message = await send_reactivation_email_3(user, dry_run=dry_run)

        if success:
            if dry_run:
                skipped += 1
            else:
                sent += 1
            print(f"✅ {user.email}: {message}")
        else:
            failed += 1
            print(f"❌ {user.email}: {message}")

    # Resumo
    print("\n" + "=" * 70)
    print("📊 RESUMO FINAL DA CAMPANHA")
    print("=" * 70)
    print(f"Total processado: {total}")
    print(f"✅ Enviados com sucesso: {sent}")
    print(f"❌ Falhas: {failed}")
    if dry_run:
        print(f"🔍 Dry run (não enviados): {skipped}")
    print("\n🎉 Campanha de reativação finalizada!")
    print("=" * 70)


def main():
    """Função principal"""
    # Parse argumentos
    dry_run = '--dry-run' in sys.argv
    user_id = None

    for arg in sys.argv:
        if arg.startswith('--user-id='):
            user_id = arg.split('=')[1]

    try:
        asyncio.run(main_async(dry_run=dry_run, user_id=user_id))
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operação interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
