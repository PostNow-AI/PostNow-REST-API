"""
Quality Validator Service - Validação automática de qualidade de posts.
Detecta problemas e auto-corrige quando possível.
"""

import logging
import re
from typing import Dict, List, Optional
from dataclasses import dataclass

from IdeaBank.models import PostIdea
from Campaigns.constants import QUALITY_THRESHOLDS

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Representa um problema de qualidade detectado."""
    type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    can_auto_fix: bool
    current_value: any
    recommended_value: any
    message: str


@dataclass
class ValidationResult:
    """Resultado da validação de um post."""
    is_valid: bool
    score: float  # 0-100
    issues: List[ValidationIssue]
    auto_fixed: List[str]


class QualityValidatorService:
    """
    Valida qualidade de posts de campanha e auto-corrige quando possível.
    """
    
    MIN_QUALITY_SCORE = QUALITY_THRESHOLDS['min_harmony_score']
    
    def validate_campaign_posts(self, posts: List[PostIdea]) -> Dict:
        """
        Valida todos os posts de uma campanha.
        
        Returns:
            Dict com: passed, auto_fixed, needs_attention, failed
        """
        
        results = {
            'passed': [],
            'auto_fixed': [],
            'needs_attention': [],
            'failed': []
        }
        
        for post in posts:
            validation = self.validate_post(post)
            
            if validation.is_valid and not validation.auto_fixed:
                results['passed'].append(post)
            
            elif validation.auto_fixed:
                results['auto_fixed'].append({
                    'post': post,
                    'fixes_applied': validation.auto_fixed,
                    'issues_resolved': len(validation.auto_fixed)
                })
            
            elif validation.score >= self.MIN_QUALITY_SCORE:
                # Passou mas tem warnings
                results['needs_attention'].append({
                    'post': post,
                    'issues': [i for i in validation.issues if i.severity != 'critical'],
                    'score': validation.score
                })
            
            else:
                # Falhou validação mínima
                results['failed'].append({
                    'post': post,
                    'issues': validation.issues,
                    'score': validation.score
                })
        
        return results
    
    def validate_post(self, post: PostIdea) -> ValidationResult:
        """Valida um post individual."""
        
        issues = []
        auto_fixed = []
        
        # 1. Validar texto
        text_issues, text_fixes = self._validate_text(post)
        issues.extend(text_issues)
        auto_fixed.extend(text_fixes)
        
        # 2. Validar CTA
        cta_issues, cta_fixes = self._validate_cta(post)
        issues.extend(cta_issues)
        auto_fixed.extend(cta_fixes)
        
        # 3. Validar imagem (se houver)
        if post.image_url:
            image_issues = self._validate_image(post)
            issues.extend(image_issues)
        
        # 4. Validar hashtags
        hashtag_issues, hashtag_fixes = self._validate_hashtags(post)
        issues.extend(hashtag_issues)
        auto_fixed.extend(hashtag_fixes)
        
        # Calcular score
        score = self._calculate_quality_score(issues)
        
        # Determinar se é válido
        critical_issues = [i for i in issues if i.severity == 'critical']
        is_valid = len(critical_issues) == 0 and score >= self.MIN_QUALITY_SCORE
        
        return ValidationResult(
            is_valid=is_valid,
            score=score,
            issues=issues,
            auto_fixed=auto_fixed
        )
    
    def _validate_text(self, post: PostIdea) -> tuple[List[ValidationIssue], List[str]]:
        """Valida comprimento e qualidade do texto."""
        
        issues = []
        fixes = []
        
        text_length = len(post.content)
        min_length = QUALITY_THRESHOLDS['min_text_length']
        max_length = QUALITY_THRESHOLDS['max_text_length']
        ideal_min, ideal_max = QUALITY_THRESHOLDS['ideal_text_length']
        
        # Muito longo
        if text_length > max_length:
            issues.append(ValidationIssue(
                type='text_too_long',
                severity='medium',
                can_auto_fix=True,
                current_value=text_length,
                recommended_value=ideal_max,
                message=f'Texto muito longo ({text_length} caracteres). Ideal: {ideal_min}-{ideal_max}.'
            ))
            
            # Auto-fix: Resumir usando IA
            try:
                post.content = self._auto_summarize(post.content, max_length=ideal_max)
                post.save()
                fixes.append('text_summarized')
                logger.info(f"Post {post.id}: Texto resumido automaticamente")
            except Exception as e:
                logger.error(f"Falha ao resumir texto: {str(e)}")
        
        # Muito curto
        elif text_length < min_length:
            issues.append(ValidationIssue(
                type='text_too_short',
                severity='medium',
                can_auto_fix=False,
                current_value=text_length,
                recommended_value=min_length,
                message=f'Texto muito curto ({text_length} caracteres). Mínimo: {min_length}.'
            ))
        
        return issues, fixes
    
    def _validate_cta(self, post: PostIdea) -> tuple[List[ValidationIssue], List[str]]:
        """Valida presença de Call-to-Action."""
        
        issues = []
        fixes = []
        
        if not self._has_cta(post.content):
            issues.append(ValidationIssue(
                type='missing_cta',
                severity='low',
                can_auto_fix=True,
                current_value=False,
                recommended_value=True,
                message='Post não tem call-to-action claro.'
            ))
            
            # Auto-fix: Adicionar CTA genérico
            try:
                cta = self._generate_generic_cta(post)
                post.content += f"\n\n{cta}"
                post.save()
                fixes.append('cta_added')
                logger.info(f"Post {post.id}: CTA adicionado automaticamente")
            except Exception as e:
                logger.error(f"Falha ao adicionar CTA: {str(e)}")
        
        return issues, fixes
    
    def _validate_image(self, post: PostIdea) -> List[ValidationIssue]:
        """Valida imagem (básico - análise profunda em outro service)."""
        
        issues = []
        
        # Verificar se image_url está vazia
        if not post.image_url or post.image_url.strip() == '':
            issues.append(ValidationIssue(
                type='missing_image',
                severity='high',
                can_auto_fix=False,
                current_value=None,
                recommended_value='URL válida',
                message='Imagem não foi gerada.'
            ))
        
        return issues
    
    def _validate_hashtags(self, post: PostIdea) -> tuple[List[ValidationIssue], List[str]]:
        """Valida presença de hashtags."""
        
        issues = []
        fixes = []
        
        hashtag_pattern = r'#\w+'
        hashtags = re.findall(hashtag_pattern, post.content)
        
        if len(hashtags) == 0:
            issues.append(ValidationIssue(
                type='missing_hashtags',
                severity='low',
                can_auto_fix=True,
                current_value=0,
                recommended_value=(2, 5),
                message='Post não tem hashtags.'
            ))
            
            # Auto-fix: Adicionar hashtags genéricas
            # (lógica completa de hashtags em outro service)
            # Por ora, não adicionar automaticamente
        
        elif len(hashtags) > 10:
            issues.append(ValidationIssue(
                type='too_many_hashtags',
                severity='low',
                can_auto_fix=False,
                current_value=len(hashtags),
                recommended_value=(2, 5),
                message=f'Muitas hashtags ({len(hashtags)}). Ideal: 2-5.'
            ))
        
        return issues, fixes
    
    def _calculate_quality_score(self, issues: List[ValidationIssue]) -> float:
        """Calcula score de qualidade (0-100)."""
        
        if not issues:
            return 100.0
        
        # Penalidades por severidade
        penalties = {
            'low': 5,
            'medium': 15,
            'high': 30,
            'critical': 50
        }
        
        total_penalty = sum(penalties[issue.severity] for issue in issues)
        score = max(0, 100 - total_penalty)
        
        return score
    
    def _has_cta(self, text: str) -> bool:
        """Detecta se texto tem call-to-action."""
        
        cta_patterns = [
            r'\bagende\b', r'\bclique\b', r'\bacesse\b', r'\bsaiba mais\b',
            r'\bconheça\b', r'\bfale comigo\b', r'\bentre em contato\b',
            r'\bwhatsapp\b', r'\bdm\b', r'\blink\b', r'\bbio\b',
            r'\bgaranta\b', r'\bcompre\b', r'\badquira\b',
        ]
        
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in cta_patterns)
    
    def _generate_generic_cta(self, post: PostIdea) -> str:
        """Gera CTA genérico baseado no objetivo do post."""
        
        # CTAs genéricos por objetivo
        ctas = {
            'awareness': '💬 Comente se você já passou por isso!',
            'engagement': '👉 Compartilhe com quem precisa saber disso!',
            'sales': '📲 Fale comigo no WhatsApp para saber mais!',
            'branding': '💡 Acompanhe para mais conteúdos assim!',
            'education': '📚 Salve este post para consultar depois!',
            'lead_generation': '🎯 Link na bio para acessar material completo!',
        }
        
        objective = post.post.objective
        return ctas.get(objective, '💬 Comente o que achou!')
    
    def _auto_summarize(self, text: str, max_length: int) -> str:
        """
        Resumir texto automaticamente.
        Por ora, trunca inteligentemente. Em produção, usar IA.
        """
        
        if len(text) <= max_length:
            return text
        
        # Truncar em frase completa mais próxima
        truncated = text[:max_length]
        
        # Encontrar último ponto, exclamação ou interrogação
        last_sentence_end = max(
            truncated.rfind('.'),
            truncated.rfind('!'),
            truncated.rfind('?')
        )
        
        if last_sentence_end > max_length * 0.7:  # Se encontrou ponto razoável
            return truncated[:last_sentence_end + 1]
        else:
            return truncated[:max_length] + '...'
    
    def attempt_auto_recovery(self, post: PostIdea, max_attempts: int = 3) -> bool:
        """
        Tenta recuperar post que falhou validação.
        Regenera silenciosamente até 3x.
        """
        
        for attempt in range(max_attempts):
            logger.info(f"Tentativa {attempt + 1} de regenerar post {post.id}")
            
            try:
                # Regenerar post
                # (Lógica completa em outro service)
                # Por ora, retornar False
                return False
            
            except Exception as e:
                logger.error(f"Falha na tentativa {attempt + 1}: {str(e)}")
                continue
        
        return False

