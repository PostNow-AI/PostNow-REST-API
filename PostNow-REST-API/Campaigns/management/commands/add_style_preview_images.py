"""
Management command para adicionar imagens de preview aos estilos.
Usa placeholder.com para gerar imagens temporárias.
"""

from django.core.management.base import BaseCommand
from Campaigns.models import VisualStyle


class Command(BaseCommand):
    help = 'Adiciona URLs de preview de imagens aos estilos visuais'
    
    def handle(self, *args, **options):
        """
        Adiciona imagens placeholder para cada estilo.
        Formato: https://via.placeholder.com/300x300/{cor}/{texto}
        """
        
        # Mapeamento de cores por categoria para placeholder
        style_colors = {
            # Minimalistas - tons neutros
            'minimal_clean': ('FFFFFF', 'EEEEEE', 'Minimal'),
            'scandinavian': ('F5F5F5', 'E0E0E0', 'Scandi'),
            'japanese_zen': ('FAFAFA', 'CCCCCC', 'Zen'),
            
            # Corporativos - azuis
            'corporate_blue': ('1E40AF', 'FFFFFF', 'Corporate'),
            'executive_clean': ('334155', 'FFFFFF', 'Executive'),
            'tech_modern': ('3B82F6', 'FFFFFF', 'Tech'),
            'legal_pro': ('1F2937', 'FFFFFF', 'Legal'),
            'financial_clean': ('059669', 'FFFFFF', 'Financial'),
            
            # Bold - vibrantes
            'bold_colorful': ('EC4899', 'FFFFFF', 'Bold'),
            'neon_pop': ('A855F7', 'FFFF00', 'Neon'),
            'gradient_explosion': ('8B5CF6', 'FFFFFF', 'Gradient'),
            'retro_80s': ('F59E0B', 'FF00FF', 'Retro'),
            
            # Modernos - gradientes suaves
            'modern_gradient': ('6366F1', 'FFFFFF', 'Modern'),
            'flat_design': ('14B8A6', 'FFFFFF', 'Flat'),
            'material_design': ('3B82F6', 'FFFFFF', 'Material'),
            
            # Criativos - artísticos
            'hand_drawn': ('FDE047', '422006', 'Hand'),
            'watercolor': ('C084FC', 'FFFFFF', 'Water'),
            'collage_aesthetic': ('FB923C', 'FFFFFF', 'Collage'),
        }
        
        updated_count = 0
        
        for slug, (bg_color, text_color, text) in style_colors.items():
            try:
                style = VisualStyle.objects.get(slug=slug)
                
                # Gerar URL de placeholder
                # Formato: https://via.placeholder.com/300/{bg_color}/{text_color}?text={text}
                preview_url = f"https://via.placeholder.com/300/{bg_color}/{text_color}?text={text}"
                
                style.preview_image_url = preview_url
                style.save(update_fields=['preview_image_url'])
                
                updated_count += 1
                self.stdout.write(f"  ✓ {style.name}: {preview_url}")
                
            except VisualStyle.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ Estilo não encontrado: {slug}")
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✅ {updated_count} estilos atualizados com imagens!")
        )

