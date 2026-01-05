"""
Management command para popular exemplos seed de estilos visuais.

Gera 1 exemplo contextualizado de CADA estilo (20 total).
Custo: $0.23 × 20 = $4.60 (UMA VEZ!)

Estratégia (ideia do Rogério):
- Cria briefings realistas para cada categoria
- Gera imagem com o estilo aplicado
- Salva como exemplo público
- Galeria cresce depois com posts reais de usuários
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from Campaigns.models import VisualStyle, VisualStyleExample
from services.ai_service import AiService
from services.s3_sevice import S3Service
from google.genai import types

User = get_user_model()


class Command(BaseCommand):
    help = 'Gera exemplos seed de estilos visuais (1 por estilo)'
    
    def handle(self, *args, **options):
        """Gera 20 exemplos contextualizados (seeds)."""
        
        self.stdout.write("\n🎨 GERANDO EXEMPLOS SEED DE ESTILOS VISUAIS")
        self.stdout.write("=" * 60)
        
        # Pegar admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR("❌ Superusuário não encontrado"))
            return
        
        # Inicializar serviços
        ai_service = AiService()
        s3_service = S3Service()
        
        # Briefings genéricos mas realistas por categoria
        category_briefings = self._get_category_briefings()
        
        generated_count = 0
        failed_count = 0
        
        for style in VisualStyle.objects.filter(is_active=True).order_by('sort_order'):
            # Verificar se já tem exemplo seed
            if VisualStyleExample.objects.filter(visual_style=style, is_seed=True).exists():
                self.stdout.write(f"  ⏭️  {style.name}: já tem exemplo seed")
                continue
            
            try:
                self.stdout.write(f"\n🎨 Gerando exemplo para: {style.name} ({style.category})")
                
                # Pegar briefing apropriado para a categoria
                briefing = category_briefings.get(style.category, category_briefings['general'])
                
                # Construir prompt personalizado
                prompt = self._build_contextual_prompt(style, briefing)
                
                # Gerar imagem com Gemini
                image_result = ai_service.generate_image(
                    prompt_list=[prompt],
                    image_attachment=None,
                    user=admin_user,
                    config=types.GenerateContentConfig(
                        temperature=0.8,
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio="1:1")
                    )
                )
                
                if image_result:
                    # Upload para S3
                    image_url = s3_service.upload_image(admin_user, image_result)
                    
                    # Criar exemplo
                    VisualStyleExample.objects.create(
                        visual_style=style,
                        image_url=image_url,
                        content_preview=briefing['preview'],
                        is_seed=True,
                        is_featured=(generated_count < 6)  # Primeiros 6 são featured
                    )
                    
                    generated_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Salvo: {image_url[:60]}..."))
                else:
                    failed_count += 1
                    self.stdout.write(self.style.WARNING(f"  ⚠ Falha na geração"))
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f"  ✗ Erro: {str(e)}"))
                continue
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Concluído! {generated_count} exemplos gerados, {failed_count} falharam."
            )
        )
        self.stdout.write(f"\n💰 Custo estimado: ${generated_count * 0.23:.2f}")
        self.stdout.write(f"📊 Total de exemplos no sistema: {VisualStyleExample.objects.count()}")
    
    def _get_category_briefings(self):
        """Briefings realistas por categoria de estilo."""
        return {
            'minimalista': {
                'objective': 'Lançamento de serviço de consultoria empresarial',
                'preview': 'Apresentando nossa nova metodologia de transformação digital...'
            },
            'corporativo': {
                'objective': 'Campanha educacional sobre compliance jurídico',
                'preview': 'Entenda as novas regulamentações de proteção de dados...'
            },
            'bold': {
                'objective': 'Promoção de Black Friday para e-commerce de moda',
                'preview': '🔥 Descontos de até 70% em peças selecionadas! Aproveite...'
            },
            'criativo': {
                'objective': 'Showcase de portfólio de design gráfico',
                'preview': 'Cada projeto conta uma história única. Veja nosso trabalho...'
            },
            'moderno': {
                'objective': 'Lançamento de produto tech/SaaS',
                'preview': 'Revolucione sua produtividade com inteligência artificial...'
            },
            'professional': {
                'objective': 'Campanha de autoridade em saúde e bem-estar',
                'preview': 'Dicas baseadas em ciência para uma vida mais saudável...'
            },
            'general': {
                'objective': 'Campanha de engajamento e crescimento de audiência',
                'preview': 'Conteúdo de valor para você crescer no Instagram...'
            }
        }
    
    def _build_contextual_prompt(self, style, briefing):
        """Constrói prompt contextualizado para gerar exemplo."""
        
        # Base do prompt
        base = f"""Create a professional Instagram post image (1080x1080px) for:

CAMPAIGN: {briefing['objective']}
CONTENT: {briefing['preview']}

VISUAL STYLE: {style.name} - {style.description}

STYLE CHARACTERISTICS:"""
        
        # Adicionar modificadores do estilo
        if style.image_prompt_modifiers:
            modifiers = style.image_prompt_modifiers
            if isinstance(modifiers, str):
                import json
                try:
                    modifiers = json.loads(modifiers)
                except:
                    modifiers = []
            
            for modifier in modifiers:
                base += f"\n- {modifier}"
        
        # Adicionar categoria específica
        base += f"\n\nCATEGORY: {style.category}"
        base += f"\n\nCreate a visually striking, professional Instagram post that exemplifies this style."
        base += f"\nMake it realistic and representative of what users would create."
        
        return base

