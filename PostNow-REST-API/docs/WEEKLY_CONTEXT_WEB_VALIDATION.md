# Weekly Context Web - Validação End-to-End

Este documento fornece um checklist completo para validação do Radar Semanal (Weekly Context Web Page).

## Pré-requisitos

Antes de iniciar a validação:

1. **Backend rodando**: Django development server ou deploy em produção
2. **Frontend rodando**: Vite dev server ou build de produção
3. **Usuário de teste**: Com CreatorProfile configurado
4. **Weekly Context gerado**: Executar script de geração ou aguardar cron job

## Checklist de Validação

### ✅ 1. Geração de Dados

- [ ] Gerar Weekly Context via script para usuário de teste
  ```bash
  cd PostNow-REST-API
  python scripts/trigger_team_validation.py
  ```
- [ ] Verificar que dados foram salvos em `ClientContextHistory`
- [ ] Confirmar estrutura `tendencies_data` com `ranked_opportunities`

### ✅ 2. Autenticação e Acesso

- [ ] Fazer login como usuário de teste no frontend
- [ ] Verificar token JWT armazenado nos cookies
- [ ] Confirmar que usuário tem permissão `IsAuthenticated`

### ✅ 3. Navegação no Menu

- [ ] Localizar item "Radar Semanal" no menu lateral (somente para admins)
- [ ] Verificar ícone Radio está renderizado corretamente
- [ ] Clicar no item "Radar Semanal"
- [ ] Confirmar redirecionamento para `/weekly-context`

### ✅ 4. Carregamento da Página

- [ ] Verificar loading state (skeleton cards) aparece inicialmente
- [ ] Confirmar chamada API para `/api/v1/client-context/weekly-context/`
- [ ] Verificar resposta 200 OK com estrutura esperada:
  ```json
  {
    "success": true,
    "data": {
      "week_range": "DD/MM a DD/MM",
      "business_name": "Nome da Empresa",
      "has_previous": boolean,
      "has_next": boolean,
      "ranked_opportunities": { ... }
    }
  }
  ```

### ✅ 5. Renderização do Header

- [ ] Verificar título "📡 Radar Semanal de Conteúdo"
- [ ] Confirmar nome do negócio exibido corretamente
- [ ] Verificar intervalo de datas (week_range) formatado
- [ ] Botão "Anterior" habilitado se `has_previous === true`
- [ ] Botão "Próxima" habilitado se `has_next === true`

### ✅ 6. Exibição de Matérias e Assuntos

- [ ] Verificar todas as seções renderizadas na ordem:
  - 🔥 Polêmica & Debate
  - 📚 Educativo & Dicas
  - 📰 Newsjacking
  - 🔮 Futuro
  - 📊 Estudo de Caso
  - 🎭 Entretenimento
  - 💡 Outros
- [ ] Confirmar badge de contagem correto em cada seção
- [ ] Verificar primeira seção (Polêmica) expandida por padrão

### ✅ 7. Interação com Accordion

- [ ] Expandir uma seção colapsada (clicar no header)
- [ ] Verificar ícone muda de ChevronRight para ChevronDown
- [ ] Confirmar cards de oportunidades aparecem
- [ ] Colapsar seção expandida
- [ ] Verificar cards são ocultados

### ✅ 8. Cards de Oportunidade

Para cada card:
- [ ] Verificar título da ideia exibido
- [ ] Confirmar badge de score com cor correta por tipo
- [ ] Verificar "Por que viraliza" renderizado
- [ ] Confirmar "Sugestão" (gatilho criativo) em caixa colorida
- [ ] Botão "Ver Fonte" presente e funcional
- [ ] Botão "Criar Post" presente e funcional

### ✅ 9. Ação "Ver Fonte"

- [ ] Clicar em "Ver Fonte" em um card
- [ ] Verificar nova aba/janela abre com `url_fonte`
- [ ] Confirmar link válido e carrega corretamente

### ✅ 10. Ação "Criar Post"

- [ ] Clicar em "Criar Post" em um card
- [ ] Verificar redirecionamento para `/ideabank`
- [ ] Confirmar query params presentes:
  - `?context=weekly`
  - `&title={titulo_ideia}`
  - `&description={gatilho_criativo}`
- [ ] Verificar dialog de criação abre automaticamente
- [ ] Confirmar campos pré-preenchidos:
  - Nome: `titulo_ideia`
  - Detalhes: `gatilho_criativo`
- [ ] Verificar query params são limpos após pré-preenchimento

### ✅ 11. Navegação Entre Semanas

**Semana Anterior:**
- [ ] Clicar no botão "Anterior" (se habilitado)
- [ ] Verificar chamada API para `/api/v1/client-context/weekly-context/history/?offset=1`
- [ ] Confirmar dados da semana anterior carregam
- [ ] Verificar flags `has_next=true` e `has_previous` atualizado
- [ ] Confirmar `week_range` diferente

**Próxima Semana:**
- [ ] Clicar no botão "Próxima" (se habilitado)
- [ ] Verificar offset decrementa (offset=0 para semana atual)
- [ ] Confirmar retorno à semana atual
- [ ] Verificar `has_next=false` quando na semana atual

### ✅ 12. Estados de Erro

**Usuário sem dados:**
- [ ] Testar com usuário que não tem Weekly Context
- [ ] Verificar Empty State renderizado:
  - Ícone RadioTower grande
  - Mensagem "Nenhuma oportunidade disponível"
  - Sugestão de aguardar próximo ciclo

**Erro de API:**
- [ ] Simular erro 500 (desligar backend temporariamente)
- [ ] Verificar Error State renderizado:
  - Ícone AlertCircle
  - Mensagem de erro
  - Botão "Tentar Novamente"
- [ ] Clicar em "Tentar Novamente"
- [ ] Confirmar nova chamada API executada

**Usuário não autenticado:**
- [ ] Fazer logout
- [ ] Tentar acessar `/weekly-context` diretamente
- [ ] Verificar redirecionamento para `/login`
- [ ] Confirmar 401 Unauthorized

### ✅ 13. Responsividade Mobile

Testar em viewport mobile (375px de largura):
- [ ] Header adaptado (texto menor, botões compactos)
- [ ] Cards empilhados verticalmente
- [ ] Accordion funciona corretamente
- [ ] Botões "Ver Fonte" e "Criar Post" responsivos
- [ ] Navegação entre semanas funcional

### ✅ 14. Dark Mode

- [ ] Alternar para dark mode
- [ ] Verificar cores adaptadas:
  - Background escuro
  - Texto claro
  - Cards com contraste adequado
- [ ] Confirmar badges legíveis
- [ ] Verificar gradient do header

### ✅ 15. Performance

- [ ] Verificar tempo de carregamento inicial < 2s
- [ ] Confirmar cache TanStack Query funcionando:
  - Navegar para outra página
  - Voltar para `/weekly-context`
  - Verificar dados carregam do cache (sem loading)
- [ ] Testar navegação entre semanas (deve ser rápida)

### ✅ 16. Testes Backend

Executar testes unitários:
```bash
cd PostNow-REST-API
python manage.py test ClientContext.tests.WeeklyContextAPITests
```

Verificar todos os testes passam:
- [ ] `test_weekly_context_current_authenticated`
- [ ] `test_weekly_context_current_no_data`
- [ ] `test_weekly_context_current_unauthenticated`
- [ ] `test_weekly_context_history_with_offset`
- [ ] `test_weekly_context_history_invalid_offset`
- [ ] `test_has_previous_has_next_flags`

### ✅ 17. Logs e Telemetria

No console do navegador:
- [ ] Verificar ausência de erros JavaScript
- [ ] Confirmar chamadas API logadas (network tab)
- [ ] Verificar warnings de deprecação resolvidos

No backend:
- [ ] Verificar logs estruturados das views
- [ ] Confirmar ausência de erros 500
- [ ] Verificar queries SQL otimizadas (não há N+1)

## Casos de Uso Reais

### Cenário 1: Criador de Conteúdo Tech

1. Login como criador de conteúdo tech
2. Acessar Radar Semanal
3. Verificar oportunidades de "Newsjacking" (notícias tech)
4. Clicar em oportunidade sobre IA
5. Criar post a partir da oportunidade
6. Verificar post criado no IdeaBank

### Cenário 2: Agência de Marketing

1. Login como admin (agência)
2. Navegar entre semanas anteriores
3. Comparar oportunidades semana a semana
4. Identificar tendências recorrentes
5. Exportar (screenshot) para relatório cliente

### Cenário 3: Negócio Local

1. Login como negócio local (restaurante)
2. Verificar seção "Sazonalidade" (se implementada)
3. Clicar em oportunidade de data comemorativa
4. Criar post promocional
5. Verificar link da fonte para inspiração

## Critérios de Aceitação

Para que a feature seja considerada **validada e pronta para produção**, todos os itens abaixo devem ser **✅**:

- [ ] Todos os checkboxes deste documento marcados
- [ ] 100% dos testes backend passando
- [ ] Zero erros de linter (backend e frontend)
- [ ] Zero erros de console no navegador
- [ ] Performance dentro do esperado (< 2s carregamento)
- [ ] Responsividade mobile validada
- [ ] Dark mode funcional
- [ ] Integração IdeaBank funcionando
- [ ] Navegação entre semanas sem bugs
- [ ] Empty states e error states renderizados corretamente

## Próximos Passos (Pós-Validação)

Após validação completa:

1. ✅ Merge da branch para `main`/`develop`
2. ✅ Deploy em staging
3. ✅ Validação final em staging
4. ✅ Deploy em produção
5. ✅ Monitoramento de logs e métricas
6. ✅ Coleta de feedback de usuários beta

---

**Data de Validação**: ___/___/______  
**Validado por**: ___________________  
**Status**: [ ] Aprovado [ ] Pendente [ ] Rejeitado

