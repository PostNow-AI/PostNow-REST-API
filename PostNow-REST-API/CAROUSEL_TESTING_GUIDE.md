# 🧪 Guia de Testes para Carrosséis Instagram

> **Documento Complementar:** CAROUSEL_IMPLEMENTATION_GUIDE.md  
> **Objetivo:** Casos de teste e validação de qualidade

---

## 📋 Casos de Teste

### Teste 1: Geração Básica de Carrossel

```python
def test_basic_carousel_generation():
    """Teste mínimo viável - gerar carrossel de 7 slides."""
    
    # Arrange
    user = User.objects.get(id=1)
    theme = "5 dicas para aumentar engajamento no Instagram"
    
    # Act
    carousel = CarouselGenerationService().generate_carousel(
        user=user,
        theme=theme,
        narrative_type='list',
        slide_count=7,
        logo_placement='first_last'
    )
    
    # Assert
    assert carousel is not None
    assert carousel.slides.count() == 7
    assert carousel.narrative_type == 'list'
    assert carousel.slides.first().image_url != ''
    assert carousel.slides.last().image_url != ''
    assert carousel.slides.first().has_arrow == True
    assert carousel.slides.first().has_numbering == True
```

### Teste 2: Análise Semântica

```python
def test_semantic_analysis_integration():
    """Verifica reuso do sistema de análise semântica em 3 etapas."""
    
    user = User.objects.get(id=1)
    service = CarouselGenerationService()
    
    # Deve reusar DailyIdeasService
    semantic_analysis = service._perform_semantic_analysis(
        user, 
        "Como aumentar seguidores no Instagram"
    )
    
    assert 'analise_semantica' in semantic_analysis
    assert semantic_analysis['analise_semantica'] is not None
```

### Teste 3: Logo Placement

```python
def test_logo_placement_strategies():
    """Testa diferentes estratégias de logo."""
    
    user = User.objects.get(id=1)
    
    # Test 1: first_last
    carousel1 = generate_test_carousel(user, logo_placement='first_last')
    assert carousel1.slides.first().has_logo == True
    assert carousel1.slides.last().has_logo == True
    assert carousel1.slides.all()[3].has_logo == False
    
    # Test 2: all_minimal
    carousel2 = generate_test_carousel(user, logo_placement='all_minimal')
    for slide in carousel2.slides.all():
        assert slide.has_logo == True
```

### Teste 4: Consistência Visual

```python
def test_visual_consistency():
    """Valida consistência visual entre slides."""
    
    carousel = generate_test_carousel(user)
    
    # Validar paleta de cores
    colors = [slide.background_color for slide in carousel.slides.all()]
    consistency_score = calculate_color_consistency(colors)
    assert consistency_score > 85  # 85% mínimo
    
    # Validar tipografia
    # (Mock - na prática seria análise da imagem)
    assert all_slides_use_same_font_family(carousel)
```

---

## 🎯 Métricas de Qualidade

```yaml
Métricas Essenciais:
  swipe_through_rate: "> 50%"
  completion_rate: "> 40%"
  visual_consistency_score: "> 85"
  text_legibility_score: "> 90"
  load_time: "< 3s por slide"
  
Benchmark por Tipo:
  tutorial: "completion_rate > 70%"
  list: "completion_rate > 55%"
  story: "completion_rate > 50%"
```

---

## ✅ Checklist de Validação

```markdown
PRÉ-PUBLICAÇÃO:
- [ ] Todos os slides gerados (nenhum vazio)
- [ ] Imagens em alta resolução (1080x1350 ou 1080x1080)
- [ ] Texto legível em mobile (teste real)
- [ ] Contraste adequado (4.5:1 mínimo)
- [ ] Logo visível mas não dominante
- [ ] Elementos de swipe presentes
- [ ] Cores harmônicas
- [ ] Numeração correta (1/7, 2/7, ...)
- [ ] CTA claro no último slide
- [ ] Testado em preview Instagram
```

---

_Documento atualizado: Janeiro 2025_

