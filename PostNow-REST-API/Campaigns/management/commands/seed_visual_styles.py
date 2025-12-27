"""
Management command para popular estilos visuais.
Cria 18 estilos curados para MVP.
"""

from django.core.management.base import BaseCommand
from Campaigns.models import VisualStyle


class Command(BaseCommand):
    help = 'Cria estilos visuais iniciais para o sistema de campanhas'
    
    def handle(self, *args, **options):
        """Cria 18 estilos visuais curados."""
        
        styles_data = [
            # MINIMALISTAS (6)
            {
                'name': 'Minimal Clean',
                'slug': 'minimal_clean',
                'category': 'minimal',
                'description': 'Minimalista limpo com muito espaço em branco',
                'tags': ['profissional', 'clean', 'moderno', 'simples'],
                'global_success_rate': 0.79,
                'success_rate_by_niche': {
                    'legal': 0.82, 'consulting': 0.84, 'tech': 0.78, 'health': 0.75
                },
                'image_prompt_modifiers': ['minimalist composition', 'clean white space', 'simple elegant'],
                'best_for_campaign_types': ['branding', 'education', 'portfolio'],
                'best_for_niches': ['legal', 'consulting', 'health', 'tech'],
                'sort_order': 1
            },
            {
                'name': 'Scandinavian Style',
                'slug': 'scandinavian',
                'category': 'minimal',
                'description': 'Estilo escandinavo: tons neutros e naturais',
                'tags': ['natural', 'neutro', 'acolhedor'],
                'global_success_rate': 0.76,
                'success_rate_by_niche': {'health': 0.81, 'wellness': 0.85},
                'best_for_campaign_types': ['branding', 'wellness'],
                'best_for_niches': ['health', 'nutrition', 'wellness'],
                'sort_order': 2
            },
            {
                'name': 'Japanese Zen',
                'slug': 'japanese_zen',
                'category': 'minimal',
                'description': 'Minimalismo japonês: equilíbrio e harmonia',
                'tags': ['zen', 'equilibrio', 'harmonioso'],
                'global_success_rate': 0.74,
                'best_for_campaign_types': ['branding', 'wellness'],
                'sort_order': 3
            },
            
            # CORPORATIVOS (5)
            {
                'name': 'Corporate Blue',
                'slug': 'corporate_blue',
                'category': 'corporate',
                'description': 'Corporativo profissional com azul predominante',
                'tags': ['corporativo', 'profissional', 'confiança', 'azul'],
                'global_success_rate': 0.84,
                'success_rate_by_niche': {
                    'legal': 0.88, 'financial': 0.91, 'consulting': 0.86
                },
                'image_prompt_modifiers': ['corporate professional', 'blue color scheme', 'trustworthy'],
                'best_for_campaign_types': ['branding', 'launch', 'education'],
                'best_for_niches': ['legal', 'financial', 'consulting'],
                'sort_order': 4
            },
            {
                'name': 'Executive Clean',
                'slug': 'executive_clean',
                'category': 'corporate',
                'description': 'Executivo elegante e sofisticado',
                'tags': ['executivo', 'elegante', 'sofisticado'],
                'global_success_rate': 0.81,
                'success_rate_by_niche': {'consulting': 0.89, 'financial': 0.85},
                'best_for_campaign_types': ['branding', 'launch'],
                'best_for_niches': ['consulting', 'financial'],
                'sort_order': 5
            },
            {
                'name': 'Tech Modern',
                'slug': 'tech_modern',
                'category': 'corporate',
                'description': 'Moderno e tecnológico',
                'tags': ['tecnologia', 'moderno', 'inovação'],
                'global_success_rate': 0.88,
                'success_rate_by_niche': {'tech': 0.93, 'saas': 0.91},
                'best_for_campaign_types': ['launch', 'education'],
                'best_for_niches': ['tech', 'saas', 'software'],
                'sort_order': 6
            },
            {
                'name': 'Legal Professional',
                'slug': 'legal_pro',
                'category': 'professional',
                'description': 'Específico para área jurídica',
                'tags': ['jurídico', 'autoridade', 'sério'],
                'global_success_rate': 0.88,
                'success_rate_by_niche': {'legal': 0.94},
                'best_for_campaign_types': ['education', 'branding'],
                'best_for_niches': ['legal', 'law'],
                'sort_order': 7
            },
            {
                'name': 'Financial Clean',
                'slug': 'financial_clean',
                'category': 'professional',
                'description': 'Para área financeira e contábil',
                'tags': ['financeiro', 'confiável', 'preciso'],
                'global_success_rate': 0.85,
                'success_rate_by_niche': {'financial': 0.92, 'accounting': 0.89},
                'best_for_campaign_types': ['education', 'branding'],
                'best_for_niches': ['financial', 'accounting'],
                'sort_order': 8
            },
            
            # BOLD & COLORFUL (4)
            {
                'name': 'Bold Colorful',
                'slug': 'bold_colorful',
                'category': 'bold',
                'description': 'Cores vibrantes e impactantes',
                'tags': ['vibrante', 'colorido', 'energético', 'jovem'],
                'global_success_rate': 0.82,
                'success_rate_by_niche': {'retail': 0.88, 'ecommerce': 0.86, 'fashion': 0.91},
                'image_prompt_modifiers': ['vibrant colors', 'bold composition', 'high energy'],
                'best_for_campaign_types': ['sales', 'engagement', 'launch'],
                'best_for_niches': ['retail', 'ecommerce', 'fashion', 'food'],
                'sort_order': 9
            },
            {
                'name': 'Neon Pop',
                'slug': 'neon_pop',
                'category': 'bold',
                'description': 'Neon vibrante estilo anos 80',
                'tags': ['neon', 'retro', 'vibrante'],
                'global_success_rate': 0.74,
                'success_rate_by_niche': {'fashion': 0.85, 'entertainment': 0.83},
                'best_for_campaign_types': ['sales', 'engagement'],
                'best_for_niches': ['fashion', 'entertainment'],
                'sort_order': 10
            },
            {
                'name': 'Gradient Explosion',
                'slug': 'gradient_explosion',
                'category': 'bold',
                'description': 'Gradientes coloridos e modernos',
                'tags': ['gradiente', 'moderno', 'digital'],
                'global_success_rate': 0.77,
                'success_rate_by_niche': {'tech': 0.82, 'creative': 0.84},
                'best_for_campaign_types': ['launch', 'branding'],
                'best_for_niches': ['tech', 'creative', 'digital'],
                'sort_order': 11
            },
            {
                'name': 'Retro 80s',
                'slug': 'retro_80s',
                'category': 'bold',
                'description': 'Retrô inspirado nos anos 80',
                'tags': ['retro', 'vintage', 'nostalgia'],
                'global_success_rate': 0.71,
                'best_for_campaign_types': ['sales', 'engagement'],
                'sort_order': 12
            },
            
            # MODERNOS (3)
            {
                'name': 'Modern Gradient',
                'slug': 'modern_gradient',
                'category': 'modern',
                'description': 'Gradientes suaves e modernos',
                'tags': ['moderno', 'gradiente', 'suave'],
                'global_success_rate': 0.80,
                'success_rate_by_niche': {'tech': 0.84, 'saas': 0.82},
                'best_for_campaign_types': ['branding', 'launch'],
                'best_for_niches': ['tech', 'saas', 'digital'],
                'sort_order': 13
            },
            {
                'name': 'Flat Design',
                'slug': 'flat_design',
                'category': 'modern',
                'description': 'Design plano moderno',
                'tags': ['flat', 'moderno', 'simples'],
                'global_success_rate': 0.78,
                'best_for_campaign_types': ['education', 'branding'],
                'sort_order': 14
            },
            {
                'name': 'Material Design',
                'slug': 'material_design',
                'category': 'modern',
                'description': 'Inspirado em Material Design do Google',
                'tags': ['material', 'google', 'moderno'],
                'global_success_rate': 0.76,
                'best_for_campaign_types': ['education', 'tech'],
                'best_for_niches': ['tech', 'saas'],
                'sort_order': 15
            },
            
            # CRIATIVOS (3)
            {
                'name': 'Hand Drawn',
                'slug': 'hand_drawn',
                'category': 'creative',
                'description': 'Ilustrações desenhadas à mão',
                'tags': ['ilustração', 'artesanal', 'único'],
                'global_success_rate': 0.73,
                'success_rate_by_niche': {'creative': 0.87, 'design': 0.89},
                'best_for_campaign_types': ['portfolio', 'branding'],
                'best_for_niches': ['creative', 'design', 'arts'],
                'sort_order': 16
            },
            {
                'name': 'Watercolor',
                'slug': 'watercolor',
                'category': 'creative',
                'description': 'Aquarela artística e suave',
                'tags': ['aquarela', 'artístico', 'suave'],
                'global_success_rate': 0.75,
                'success_rate_by_niche': {'creative': 0.86, 'design': 0.84},
                'best_for_campaign_types': ['portfolio', 'branding'],
                'best_for_niches': ['creative', 'design'],
                'sort_order': 17
            },
            {
                'name': 'Collage Aesthetic',
                'slug': 'collage_aesthetic',
                'category': 'creative',
                'description': 'Colagem criativa e artística',
                'tags': ['colagem', 'artístico', 'criativo'],
                'global_success_rate': 0.70,
                'success_rate_by_niche': {'creative': 0.82},
                'best_for_campaign_types': ['portfolio', 'engagement'],
                'best_for_niches': ['creative', 'arts'],
                'sort_order': 18
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for style_data in styles_data:
            style, created = VisualStyle.objects.update_or_create(
                slug=style_data['slug'],
                defaults=style_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"  ✓ Criado: {style.name}")
            else:
                updated_count += 1
                self.stdout.write(f"  ↻ Atualizado: {style.name}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Seeds concluídos! {created_count} criados, {updated_count} atualizados."
            )
        )

