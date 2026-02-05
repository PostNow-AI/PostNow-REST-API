#!/usr/bin/env python3
"""
Script para enviar o primeiro email da campanha de reativação.
Envia para usuários que tiveram assinatura até 25/12/2025 e não reativaram.

Assunto: Apenas um obrigado (e algumas novidades por aqui)
Timing: Dia 1 (executar imediatamente)

Uso:
    python scripts/reactivation_email_1.py [--dry-run] [--user-id=<uuid>]
"""
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

import django
from asgiref.sync import sync_to_async

# Adiciona o diretório raiz ao Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configura o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sonora_REST_API.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils import timezone

from CreditSystem.models import UserSubscription
from OnboardingCampaign.models import ReactivationEmail
from services.mailjet_service import MailjetService

User = get_user_model()


async def get_target_users():
    """
    Retorna usuários elegíveis para o email 1 de reativação.

    Critérios:
    - Tiveram assinatura que terminou em/antes de 25/12/2025
    - NÃO reativaram desde então
    - NÃO receberam este email antes
    """
    cutoff_date = timezone.make_aware(datetime(2025, 12, 25, 23, 59, 59))

    # Usuários com assinatura cancelada/expirada até 25/12/2025
    users_with_expired_subs = await sync_to_async(lambda: UserSubscription.objects.filter(
        status__in=['cancelled', 'expired'],
        end_date__isnull=False,
        end_date__lte=cutoff_date
    ).values_list('user_id', flat=True).distinct())()

    # Usuários que reativaram após 25/12/2025
    users_who_reactivated = await sync_to_async(lambda: UserSubscription.objects.filter(
        status='active',
        start_date__gt=cutoff_date
    ).values_list('user_id', flat=True).distinct())()

    # Usuários que já receberam este email
    users_already_sent = await sync_to_async(lambda: ReactivationEmail.objects.filter(
        email_number=ReactivationEmail.EMAIL_1,
        sent_at__isnull=False
    ).values_list('user_id', flat=True).distinct())()

    # Convert to lists for printing
    users_with_expired_subs_list = await sync_to_async(lambda: list(users_with_expired_subs))()
    users_who_reactivated_list = await sync_to_async(lambda: list(users_who_reactivated))()
    users_already_sent_list = await sync_to_async(lambda: list(users_already_sent))()

    print(f'Users with expired subs: {users_with_expired_subs_list}')
    print(f'Users who reactivated: {users_who_reactivated_list}')
    print(f'Users already sent: {users_already_sent_list}')
    # Filtra usuários elegíveis
    target_users = await sync_to_async(lambda: User.objects.filter(
        id__in=users_with_expired_subs_list
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


async def send_reactivation_email_1(user, dry_run=False):
    """
    Envia o primeiro email de reativação para um usuário.

    Args:
        user: Instância de User
        dry_run: Se True, apenas simula o envio

    Returns:
        tuple: (success, message)
    """
    try:
        # Verifica se já enviou
        existing = await sync_to_async(ReactivationEmail.objects.filter(
            user=user,
            email_number=ReactivationEmail.EMAIL_1
        ).first)()

        if existing and existing.sent_at:
            return False, f"Email 1 já enviado em {existing.sent_at}"

        # Prepara contexto do template
        frontend_url = os.getenv('FRONTEND_URL', 'https://postnow.app')
        context = {
            'user_name': user.first_name or user.username or 'Olá',
            'current_year': datetime.now().year,
            'frontend_url': frontend_url
        }

        # Renderiza template
        html_content = await sync_to_async(render_to_string)('reactivation/email_1.html', context)
        subject = "Apenas um obrigado (e algumas novidades por aqui)"

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
                    email_number=ReactivationEmail.EMAIL_1,
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
    print("📧 CAMPANHA DE REATIVAÇÃO - EMAIL 1")
    print("Assunto: Apenas um obrigado (e algumas novidades por aqui)")
    print("=" * 70)

    if dry_run:
        print("\n🔍 MODO DRY RUN - Nenhum email será enviado\n")

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
        print(f"\n⚠️  Você está prestes a enviar {total} emails.")
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
        success, message = await send_reactivation_email_1(user, dry_run=dry_run)

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
    print("📊 RESUMO")
    print("=" * 70)
    print(f"Total processado: {total}")
    print(f"✅ Enviados com sucesso: {sent}")
    print(f"❌ Falhas: {failed}")
    if dry_run:
        print(f"🔍 Dry run (não enviados): {skipped}")
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
