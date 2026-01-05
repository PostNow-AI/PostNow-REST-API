import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sonora_REST_API.settings')
os.environ["USE_SQLITE"] = "True"
django.setup()

User = get_user_model()
email = 'rogeriofr86@gmail.com'

try:
    user = User.objects.get(email=email)
    profile = user.creator_profile
    
    # Pegar os primeiros 3 estilos visuais do banco
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM visual_styles ORDER BY sort_order LIMIT 3")
    style_ids = [row[0] for row in cursor.fetchall()]
    
    if style_ids:
        profile.visual_style_ids = style_ids
        profile.save()
        print(f"✅ Visual styles adicionados ao perfil: {style_ids}")
        print(f"IDs: {profile.visual_style_ids}")
    else:
        print("❌ Nenhum estilo visual encontrado no banco")
        
except User.DoesNotExist:
    print(f"Usuário {email} não encontrado")
except Exception as e:
    print(f"Erro: {e}")
