#!/usr/bin/env python
"""
Script para diagnosticar problemas com Mailjet.
"""
import os
import sys
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def diagnose_mailjet():
    """Diagnóstico completo do Mailjet."""
    api_key = os.getenv('MJ_APIKEY_PUBLIC')
    api_secret = os.getenv('MJ_APIKEY_PRIVATE')

    print("=== VERIFICAÇÃO DE CONFIGURAÇÃO ===")
    print(f"MJ_APIKEY_PUBLIC: {api_key[:15]}..." if api_key else "MJ_APIKEY_PUBLIC: NÃO CONFIGURADO")
    print(f"MJ_APIKEY_PRIVATE: {api_secret[:15]}..." if api_secret else "MJ_APIKEY_PRIVATE: NÃO CONFIGURADO")
    print(f"SENDER_EMAIL: {os.getenv('SENDER_EMAIL')}")
    print(f"ADMIN_EMAILS: {os.getenv('ADMIN_EMAILS')}")

    if not api_key or not api_secret:
        print("\n❌ Credenciais não configuradas!")
        return

    auth = (api_key, api_secret)

    # 1. Verificar conta (v3)
    print("\n=== 1. STATUS DA CONTA ===")
    try:
        resp = requests.get(
            'https://api.mailjet.com/v3/REST/myprofile',
            auth=auth,
            timeout=10
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if 'Data' in data and len(data['Data']) > 0:
                profile = data['Data'][0]
                print(f"Email: {profile.get('Email')}")
                print(f"Nome: {profile.get('Firstname')} {profile.get('Lastname')}")
                print(f"Empresa: {profile.get('CompanyName')}")
        else:
            print(f"Erro: {resp.text[:200]}")
    except Exception as e:
        print(f"Erro: {e}")

    # 2. Verificar API Key
    print("\n=== 2. STATUS DA API KEY ===")
    try:
        resp = requests.get(
            'https://api.mailjet.com/v3/REST/apikey',
            auth=auth,
            timeout=10
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if 'Data' in data and len(data['Data']) > 0:
                key_info = data['Data'][0]
                print(f"IsActive: {key_info.get('IsActive')}")
                print(f"IsMaster: {key_info.get('IsMaster')}")
                print(f"Runlevel: {key_info.get('Runlevel')}")
                print(f"Name: {key_info.get('Name')}")

                # IMPORTANTE: Verificar Runlevel
                runlevel = key_info.get('Runlevel', '')
                if runlevel == 'Softlock':
                    print("\n⚠️  ATENÇÃO: Conta em SOFTLOCK - emails ficam na fila!")
                    print("   Isso geralmente significa que a conta precisa de verificação.")
                elif runlevel == 'Hardlock':
                    print("\n❌ CONTA BLOQUEADA (Hardlock) - emails não serão enviados!")
                elif runlevel == 'Normal':
                    print("\n✅ Runlevel Normal - conta deveria enviar emails normalmente.")
        else:
            print(f"Erro: {resp.text[:200]}")
    except Exception as e:
        print(f"Erro: {e}")

    # 3. Verificar sender/domínio
    print("\n=== 3. SENDERS CONFIGURADOS ===")
    try:
        resp = requests.get(
            'https://api.mailjet.com/v3/REST/sender',
            auth=auth,
            timeout=10
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if 'Data' in data:
                for sender in data['Data']:
                    print(f"\n  Email: {sender.get('Email')}")
                    print(f"  Status: {sender.get('Status')}")
                    print(f"  IsDefaultSender: {sender.get('IsDefaultSender')}")
                    print(f"  EmailType: {sender.get('EmailType')}")
        else:
            print(f"Erro: {resp.text[:200]}")
    except Exception as e:
        print(f"Erro: {e}")

    # 4. Verificar mensagens recentes
    print("\n=== 4. MENSAGENS RECENTES ===")
    try:
        resp = requests.get(
            'https://api.mailjet.com/v3/REST/message',
            auth=auth,
            params={'Limit': 5, 'Sort': 'ArrivedAt DESC'},
            timeout=10
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if 'Data' in data and len(data['Data']) > 0:
                for msg in data['Data']:
                    print(f"\n  ID: {msg.get('ID')}")
                    print(f"  Status: {msg.get('Status')}")
                    print(f"  ArrivedAt: {msg.get('ArrivedAt')}")
                    print(f"  To: {msg.get('ContactAlt', {}).get('Email', 'N/A')}")

                    # Se status é "queued", verificar motivo
                    if msg.get('Status') == 'queued':
                        print(f"  ⚠️  Mensagem na fila!")
            else:
                print("  Nenhuma mensagem encontrada.")
        else:
            print(f"Erro: {resp.text[:200]}")
    except Exception as e:
        print(f"Erro: {e}")

    # 5. Verificar estatísticas de envio
    print("\n=== 5. ESTATÍSTICAS DE ENVIO ===")
    try:
        resp = requests.get(
            'https://api.mailjet.com/v3/REST/statcounters',
            auth=auth,
            params={'CounterSource': 'APIKey', 'CounterResolution': 'Lifetime', 'CounterTiming': 'Message'},
            timeout=10
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if 'Data' in data and len(data['Data']) > 0:
                stats = data['Data'][0]
                print(f"  Total enviados: {stats.get('MessageSentCount', 0)}")
                print(f"  Total entregues: {stats.get('MessageDeliveredCount', 0)}")
                print(f"  Total bloqueados: {stats.get('MessageBlockedCount', 0)}")
                print(f"  Total spam: {stats.get('MessageSpamCount', 0)}")
                print(f"  Total bounced: {stats.get('MessageBouncedCount', 0)}")
            else:
                print("  Sem estatísticas disponíveis.")
        else:
            print(f"Erro: {resp.text[:200]}")
    except Exception as e:
        print(f"Erro: {e}")

    # 6. Verificar se há restrições na conta
    print("\n=== 6. VERIFICAÇÃO DE RESTRIÇÕES ===")
    try:
        resp = requests.get(
            'https://api.mailjet.com/v3/REST/user',
            auth=auth,
            timeout=10
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if 'Data' in data and len(data['Data']) > 0:
                user = data['Data'][0]
                print(f"  NewContactsID: {user.get('NewContactsID')}")
                print(f"  WarnedRateTimeAt: {user.get('WarnedRateTimeAt')}")
                print(f"  MaxAllowedAPIKeys: {user.get('MaxAllowedAPIKeys')}")
        else:
            print(f"Erro: {resp.text[:200]}")
    except Exception as e:
        print(f"Erro: {e}")

    print("\n" + "="*50)
    print("DIAGNÓSTICO COMPLETO")
    print("="*50)
    print("""
POSSÍVEIS CAUSAS DE EMAILS NA FILA:

1. SOFTLOCK: Conta nova precisa de verificação manual pelo Mailjet
   - Solução: Acessar dashboard Mailjet e completar verificação

2. Sender não verificado: O email remetente precisa ser validado
   - Solução: Verificar sender no dashboard Mailjet

3. Domínio não configurado: SPF/DKIM não configurados
   - Solução: Configurar DNS conforme instruções do Mailjet

4. Limite de envio atingido: Contas gratuitas têm limite diário
   - Solução: Aguardar reset ou fazer upgrade

5. Conta em revisão: Mailjet pode revisar contas novas
   - Solução: Aguardar aprovação ou contatar suporte
""")


if __name__ == '__main__':
    diagnose_mailjet()
