"""
Signals para capturar posts aprovados e transformá-los em exemplos públicos.

Estratégia automática:
1. Usuário aprova post de campanha
2. Sistema verifica se é um bom exemplo
3. Cria VisualStyleExample automaticamente
4. Galeria cresce organicamente!
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CampaignPost, VisualStyleExample, VisualStyle


@receiver(post_save, sender=CampaignPost)
def capture_approved_post_as_example(sender, instance, created, **kwargs):
    """
    Quando um post é aprovado, considera adicioná-lo à galeria pública.
    
    Critérios para virar exemplo:
    - Post aprovado
    - Tem imagem
    - Tem conteúdo
    - Estilo visual do post ainda tem poucos exemplos (<5)
    """
    
    # Só processar se for aprovação (não criação)
    if created:
        return
    
    # Verificar se foi aprovado
    if not instance.is_approved:
        return
    
    # Verificar se tem imagem e conteúdo
    if not instance.post or not instance.post.image_url:
        return
    
    # Pegar o primeiro estilo visual da campanha
    campaign = instance.campaign
    if not campaign.visual_styles or len(campaign.visual_styles) == 0:
        return
    
    # Pegar o estilo visual (primeiro da lista)
    style_id = campaign.visual_styles[0]
    
    try:
        visual_style = VisualStyle.objects.get(id=style_id)
    except VisualStyle.DoesNotExist:
        return
    
    # Verificar se esse estilo já tem muitos exemplos
    current_examples_count = VisualStyleExample.objects.filter(
        visual_style=visual_style
    ).count()
    
    if current_examples_count >= 10:  # Limite de 10 exemplos por estilo
        return
    
    # Verificar se este post já é exemplo
    if VisualStyleExample.objects.filter(post=instance).exists():
        return
    
    # Criar exemplo público
    try:
        # Pegar preview do conteúdo
        content_text = ""
        if instance.post.ideas and len(instance.post.ideas) > 0:
            first_idea = instance.post.ideas[0]
            if 'text' in first_idea:
                content_text = first_idea['text'][:200]
        
        VisualStyleExample.objects.create(
            visual_style=visual_style,
            campaign=campaign,
            post=instance,
            image_url=instance.post.image_url,
            content_preview=content_text or "Post criado por usuário",
            is_seed=False,  # Post real de usuário
            is_featured=False,  # Seeds são featured
        )
        
        print(f"✅ Post {instance.id} adicionado como exemplo de {visual_style.name}")
        
    except Exception as e:
        print(f"⚠️ Erro ao capturar exemplo: {str(e)}")

