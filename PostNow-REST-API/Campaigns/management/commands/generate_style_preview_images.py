"""
Management command para gerar imagens REAIS de posts Instagram para cada estilo.
Reutiliza código de daily_ideas_service.py (linha 390-451).
Seguindo Django Rules: Business logic em command, reutilização de services.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from google import genai
from google.genai import types
import os

from Campaigns.models import VisualStyle
from services.ai_service import AiService
from services.s3_sevice import S3Service

User = get_user_model()


class Command(BaseCommand):
    help = 'Gera imagens de preview profissionais para estilos visuais (Instagram mockups)'
    
    def handle(self, *args, **options):
        """
        Gera 18 imagens usando Gemini, seguindo estética do Instagram.
        Reutiliza AiService e S3Service existentes.
        """
        
        # Pegar admin user (ou criar um temporário)
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR("Nenhum superuser encontrado. Crie um primeiro."))
            return
        
        # Inicializar services (reutilização!)
        ai_service = AiService()
        s3_service = S3Service()
        
        # Prompts específicos por estilo (baseado em pesquisa Instagram)
        prompts = self._get_style_prompts()
        
        generated_count = 0
        failed_count = 0
        
        for style in VisualStyle.objects.all():
            try:
                self.stdout.write(f"\n🎨 Gerando imagem para: {style.name}")
                
                prompt = prompts.get(style.slug, self._get_default_prompt(style))
                
                # Gerar com Gemini (REUTILIZA AiService!)
                image_result = ai_service.generate_image(
                    prompt_list=[prompt],
                    image_attachment=None,  # Sem logo
                    user=admin_user,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(
                            aspect_ratio="1:1"  # Instagram square
                        )
                    )
                )
                
                if image_result:
                    # Upload S3 (REUTILIZA S3Service!)
                    image_url = s3_service.upload_image(admin_user, image_result)
                    
                    # Atualizar model
                    style.preview_image_url = image_url
                    style.save(update_fields=['preview_image_url'])
                    
                    generated_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Salvo: {image_url[:50]}..."))
                else:
                    failed_count += 1
                    self.stdout.write(self.style.WARNING(f"  ⚠ Falha na geração"))
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f"  ✗ Erro: {str(e)}"))
                continue
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n\n✅ Concluído! {generated_count} geradas, {failed_count} falharam."
            )
        )
    
    def _get_style_prompts(self):
        """
        Prompts profissionais baseados em pesquisa de estilos Instagram.
        Cada prompt gera mockup REAL de post Instagram.
        """
        
        return {
            'minimal_clean': """
Create Instagram post mockup (1080x1080px):

Style: Ultra minimalist (Apple/Muji aesthetic)
- Background: Pure white with subtle texture
- Content: Single centered element (simple text or minimal graphic)
- Typography: Ultra-thin sans-serif, large size
- Color: Black on white only
- Composition: 90% white space, 10% content
- Margins: 100px from all edges
- Professional, premium, breathable
- High-end product photography aesthetic
""",
            
            'corporate_blue': """
Create Instagram post mockup (1080x1080px):

Style: Corporate professional (IBM/LinkedIn)
- Layout: Navy blue header (#1E40AF) 30% top, white 70% bottom
- Content: Professional business visual (meeting or chart)
- Typography: Corporate sans-serif
- Colors: Blues and grays, white
- Composition: Structured, aligned, organized
- Trustworthy, formal, credible
- Fortune 500 company aesthetic
""",
            
            'bold_colorful': """
Create Instagram post mockup (1080x1080px):

Style: Bold vibrant (Spotify/Nike campaign)
- Background: Vibrant gradient (pink to orange)
- Content: High-impact abstract or energetic photo
- Typography: Extra bold, large
- Colors: Maximum saturation
- Composition: Dynamic, asymmetric
- Energy, youth, attention-grabbing
- Festival poster aesthetic
""",
            
            # Adicionar os 15 restantes...
            # (Simplificando para MVP, pode expandir depois)
        }
    
    def _get_default_prompt(self, style):
        """Prompt genérico baseado em categoria."""
        
        category_prompts = {
            'minimal': "Minimalist Instagram post, white background, simple elegant",
            'corporate': "Corporate professional Instagram post, blues and grays, business",
            'bold': "Bold colorful Instagram post, vibrant gradient, energetic",
            'modern': "Modern gradient Instagram post, clean contemporary",
            'creative': "Creative artistic Instagram post, hand-drawn style",
        }
        
        base = category_prompts.get(style.category, "Professional Instagram post")
        
        return f"""
Create Instagram post mockup (1080x1080px):
Style: {style.name}
Description: {style.description}
Category: {base}
Professional, high-quality, Instagram-optimized
"""

