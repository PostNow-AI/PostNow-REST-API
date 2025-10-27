from typing import Dict


class PromptService:
    def __init__(self):
        self.user = None

    def build_content_prompt(self, post_data: Dict) -> str:
        """Build the prompt for content generation based on post type."""
        post_type = post_data.get('type', '').lower()

        # Route to specific prompt based on post type
        if post_type == 'post':
            return self._build_feed_post_prompt(post_data)
        elif post_type == 'reel':
            return self._build_reel_prompt(post_data)
        elif post_type == 'story':
            return self._build_story_prompt(post_data)
        elif post_type == 'campaign':
            # Campaign uses full content prompt
            creator_profile_data = self._get_creator_profile_data()
            return self._build_automatic_post_prompt(post_data, creator_profile_data)
        else:
            # Default fallback for other types (carousel, live, etc.)
            return self._build_default_prompt(post_data)

    def _get_creator_profile_section(self) -> str:
        """Get creator profile information for prompt context."""
        creator_profile_section = ""
        if hasattr(self, 'user') and self.user:
            from CreatorProfile.models import CreatorProfile
            profile = CreatorProfile.objects.filter(user=self.user).first()
            if profile:
                creator_info = []
                if profile.professional_name:
                    creator_info.append(
                        f"Nome Profissional: {profile.professional_name}")
                if profile.profession:
                    creator_info.append(f"Profissão: {profile.profession}")
                if profile.business_name:
                    creator_info.append(f"Negócio: {profile.business_name}")
                if profile.specialization:
                    creator_info.append(
                        f"Especialização: {profile.specialization}")
                if profile.voice_tone:
                    creator_info.append(
                        f"Tom de Voz Preferido: {profile.voice_tone}")

                # Color palette
                colors = [profile.color_1, profile.color_2,
                          profile.color_3, profile.color_4, profile.color_5]
                valid_colors = [
                    color for color in colors if color and color.strip()]
                if valid_colors:
                    creator_info.append(
                        f"Paleta de Cores da Marca: {', '.join(valid_colors)}")

                if creator_info:
                    creator_profile_section = f"\n\nPERFIL DO CRIADOR:\n{chr(10).join(f'- {info}' for info in creator_info)}"

        return creator_profile_section

    def _get_creator_profile_data(self) -> dict:
        """Get creator profile data for prompt personalization."""
        profile_data = {
            'professional_name': 'Não informado',
            'profession': 'Não informado',
            'whatsapp_number': 'Não informado',
            'business_name': 'Não informado',
            'specialization': 'Não informado',
            'business_description': 'Não informado',
            'target_gender': 'Não informado',
            'target_age_range': 'Não informado',
            'target_interests': 'Não informado',
            'target_location': 'Não informado',
            'logo': 'Não fornecido',
            'color_palette': 'Não definida',
            'voice_tone': 'Profissional'
        }

        if hasattr(self, 'user') and self.user:
            from CreatorProfile.models import CreatorProfile
            profile = CreatorProfile.objects.filter(user=self.user).first()
            if profile:
                if profile.professional_name:
                    profile_data['professional_name'] = profile.professional_name
                if profile.profession:
                    profile_data['profession'] = profile.profession
                if profile.whatsapp_number:
                    profile_data['whatsapp_number'] = profile.whatsapp_number
                if profile.business_name:
                    profile_data['business_name'] = profile.business_name
                if profile.specialization:
                    profile_data['specialization'] = profile.specialization
                if profile.business_description:
                    profile_data['business_description'] = profile.business_description
                if profile.target_gender:
                    profile_data['target_gender'] = profile.target_gender
                if profile.target_age_range:
                    profile_data['target_age_range'] = profile.target_age_range
                if profile.target_interests:
                    profile_data['target_interests'] = profile.target_interests
                if profile.target_location:
                    profile_data['target_location'] = profile.target_location
                if profile.logo:
                    profile_data['logo'] = 'Logo disponível'
                if profile.voice_tone:
                    profile_data['voice_tone'] = profile.voice_tone

                # Color palette
                colors = [profile.color_1, profile.color_2,
                          profile.color_3, profile.color_4, profile.color_5]
                valid_colors = [
                    color for color in colors if color and color.strip()]
                if valid_colors:
                    profile_data['color_palette'] = ', '.join(valid_colors)

        return profile_data

    def _build_all_details(self, further_details: str) -> str:
        """Build the audience and tone section combining further details with creator profile data."""
        sections = []

        # Add further details if provided
        if further_details and further_details.strip():
            sections.append(further_details.strip())

        # # Get creator profile data for target audience and voice tone
        # if hasattr(self, 'user') and self.user:
            from CreatorProfile.models import CreatorProfile
            profile = CreatorProfile.objects.filter(user=self.user).first()
            if profile:
                audience_info = []
                brand_info = []
                if profile.business_name:
                    brand_info.append(f"Empresa: {profile.business_name}")
                if profile.profession:
                    brand_info.append(f"Profissão: {profile.profession}")
                if profile.specialization:
                    brand_info.append(
                        f"Especialização: {profile.specialization}")
                # Target audience information
                if profile.target_gender and profile.target_gender.strip():
                    audience_info.append(
                        f"Gênero do Público: {profile.target_gender}")

                if profile.target_age_range and profile.target_age_range.strip():
                    audience_info.append(
                        f"Faixa Etária: {profile.target_age_range}")

                if profile.target_location and profile.target_location.strip():
                    audience_info.append(
                        f"Localização: {profile.target_location}")

                if profile.target_interests and profile.target_interests.strip():
                    audience_info.append(
                        f"Interesses: {profile.target_interests}")

                if profile.voice_tone and profile.voice_tone.strip():
                    brand_info.append(
                        f"Tom de Voz da Marca: {profile.voice_tone}")

                colors = [profile.color_1, profile.color_2,
                          profile.color_3, profile.color_4, profile.color_5]
                valid_colors = [
                    color for color in colors if color and color.strip()]
                if valid_colors:
                    brand_info.append(
                        f"Cores da marca: {', '.join(valid_colors)}")

                if audience_info:
                    sections.append(
                        f"Dados do Público-Alvo: {' | '.join(audience_info)}")
                if brand_info:
                    sections.append(
                        f"Dados da Marca: {' | '.join(brand_info)}")
        return ' - '.join(sections) if sections else "Informações não fornecidas"

    def _build_feed_post_prompt(self, post_data: Dict) -> str:
        """Build prompt specifically for feed posts."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        details = post_data.get('further_details', '')

        # Get dynamic data from creator profile and post
        creator_profile_data = self._get_creator_profile_data()

        prompt = f"""
Você é um especialista em copywriting estratégico, criativo e persuasivo, com foco em posts de Feed para redes sociais (Instagram, Facebook, LinkedIn, etc.).

Sua missão é gerar posts de Feed completos, com base nos dados do onboarding do cliente e nos dados de entrada abaixo.

O texto deve ser fluido, natural, relevante e alinhado às tendências atuais do nicho, utilizando o método AIDA e linguagem adaptada ao público.


🧾 DADOS DE PERSONALIZAÇÃO DO CLIENTE:

Nome profissional: {creator_profile_data.get('professional_name', 'Não informado')}

Profissão: {creator_profile_data.get('profession', 'Não informado')}

Número de celular: {creator_profile_data.get('whatsapp_number', 'Não informado')}

Nome do negócio: {creator_profile_data.get('business_name', 'Não informado')}

Setor/Nicho: {creator_profile_data.get('specialization', 'Não informado')}

Descrição do negócio: {creator_profile_data.get('business_description', 'Não informado')}

Gênero do público-alvo: {creator_profile_data.get('target_gender', 'Não informado')}

Faixa etária do público-alvo: {creator_profile_data.get('target_age_range', 'Não informado')}

Interesses do público-alvo: {creator_profile_data.get('target_interests', 'Não informado')}

Localização do público-alvo: {creator_profile_data.get('target_location', 'Não informado')}

Logo: {creator_profile_data.get('logo', 'Não fornecido')}

Paleta de cores: {creator_profile_data.get('color_palette', 'Não definida')}

Tom de voz: {creator_profile_data.get('voice_tone', 'Profissional')}

🧠 DADOS DO POST:

Assunto: {name}

Objetivo: {objective}

Mais detalhes: {details}

OBJETIVO GERAL:

Criar uma copy otimizada e estratégica para post de Feed, baseada no assunto, objetivo e detalhes informados, levando em conta o contexto, o público e o tom de voz do cliente.

O conteúdo deve ser original, envolvente e alinhado com as trends atuais do tema, trazendo valor real ao público e fortalecendo a presença da marca.

🪶 REGRAS PARA O TEXTO:

Método AIDA:

Atenção: Comece com uma frase ou pergunta envolvente.

Interesse: Desenvolva o tema com empatia e relevância.

Desejo: Mostre benefícios e gere identificação.

Ação: Finalize com uma única CTA natural e coerente com o objetivo.

Estilo e tom:

Texto fluido, natural e pronto para o Feed.

Parágrafos curtos e bem espaçados.

Em média 5 emojis bem distribuídos, reforçando o tom emocional.

Respeite o tom de voz ({creator_profile_data.get('voice_tone', 'Profissional')}).

Use expressões e referências em alta no tema e no nicho.

Adapte a linguagem ao público-alvo ({creator_profile_data.get('target_gender', 'Não informado')}, {creator_profile_data.get('target_age_range', 'Não informado')}, {creator_profile_data.get('target_location', 'Não informado')}).

Evite sensacionalismo e exageros.

Personalização:

Conecte a mensagem ao negócio ({creator_profile_data.get('business_name', 'Não informado')}), ao nicho ({creator_profile_data.get('specialization', 'Não informado')}) e aos interesses do público ({creator_profile_data.get('target_interests', 'Não informado')}).

Ajuste o tom conforme o tipo de profissional e o público descrito no onboarding.

Tendências:

O conteúdo deve se basear em assuntos e comportamentos que estão em alta nas redes sociais dentro do nicho.

O texto deve parecer atual, moderno e relevante no momento da geração.

📦 FORMATO DE SAÍDA:

Gere o conteúdo exatamente neste formato:

[TEXTO COMPLETO DA COPY – fluido, natural, escaneável e com média de 5 emojis.]

Como sugestão para escrever na imagem:

Título: [Curto e criativo – até 8 palavras – diferente dos anteriores]

Subtítulo: [Frase complementar breve e envolvente – formato sempre variado]

CTA: [Chamada clara e coerente com o objetivo do post – alternada a cada campanha]

📅 CONTEXTO DE USO:

Esse prompt será usado para gerar apenas o texto do post de Feed, sem necessidade de ideias de imagem, Stories ou Reels.

Cada texto deve:

Ser diferente e original;

Refletir as tendências atuais do tema;

Manter variação diária de título, subtítulo e CTA;

Entregar um resultado de alta qualidade, digno de uma marca profissional.
"""
        return prompt.strip()

    def _build_reel_prompt(self, post_data: Dict) -> str:
        """Build prompt specifically for reels."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        details = post_data.get('further_details', '')

        creator_profile_data = self._get_creator_profile_data()
        # TODO: Replace with your specific reel prompt
        prompt = f"""
Você é um roteirista criativo e estrategista de conteúdo digital, especialista em roteiros curtos e envolventes para Reels.
Sua missão é criar roteiros personalizados de 20 a 40 segundos, com base nas informações do onboarding do cliente e nos dados de entrada do post.

O roteiro deve ser atual, estratégico, dinâmico e conectado às tendências do momento dentro do nicho do cliente.

 DADOS DE PERSONALIZAÇÃO DO CLIENTE:

Nome profissional: {creator_profile_data.get('professional_name', 'Não informado')}

Profissão: {creator_profile_data.get('profession', 'Não informado')}

Número de celular: {creator_profile_data.get('whatsapp_number', 'Não informado')}

Nome do negócio: {creator_profile_data.get('business_name', 'Não informado')}

Setor/Nicho: {creator_profile_data.get('specialization', 'Não informado')}

Descrição do negócio: {creator_profile_data.get('business_description', 'Não informado')}

Gênero do público-alvo: {creator_profile_data.get('target_gender', 'Não informado')}

Faixa etária do público-alvo: {creator_profile_data.get('target_age_range', 'Não informado')}

Interesses do público-alvo: {creator_profile_data.get('target_interests', 'Não informado')}

Localização do público-alvo: {creator_profile_data.get('target_location', 'Não informado')}

Logo: {creator_profile_data.get('logo', 'Não fornecido')}

Paleta de cores: {creator_profile_data.get('color_palette', 'Não definida')}

Tom de voz: {creator_profile_data.get('voice_tone', 'Profissional')}

🧠 DADOS DO POST:

Assunto: {name}

Objetivo: {objective}

Mais detalhes: {details}
OBJETIVO DO ROTEIRO:

Criar um roteiro de Reels (20–40 segundos) que comunique a mesma mensagem central do post de Feed, de forma dinâmica, autêntica e visualmente atraente.

O conteúdo deve:

Prender a atenção nos primeiros 3 segundos;

Ter ritmo fluido, natural e envolvente;

Ser relevante e atual dentro do nicho;

Refletir o tom, estilo e posicionamento da marca;

Estar alinhado com as tendências e formatos performáticos atuais (sons, transições, narrativas curtas e storytelling visual).

🪶 ESTRUTURA RECOMENDADA:

Abertura (0–3s):

Crie um gancho forte e direto, inspirado em trends atuais do nicho (ex: uma pergunta provocativa, frase de impacto, som popular ou movimento visual em alta).

O objetivo é capturar atenção imediata antes que o usuário role o feed.

Desenvolvimento (4–30s):

Entregue o insight principal, dica, explicação ou micro-história.

Use linguagem natural e conversacional, no estilo “fala para a câmera”.

Mantenha o ritmo com transições visuais e expressões autênticas.

Se fizer sentido, descreva gestos, cenas, enquadramentos ou ações visuais que reforcem a mensagem.

Sempre contextualize conforme o público-alvo e o tom de voz ({creator_profile_data.get('voice_tone', 'Profissional')}).

Fechamento (últimos 5–10s):

Inclua uma CTA leve e natural, coerente com o objetivo do post (ex: “Comenta aqui o que você acha”, “Salva pra lembrar depois”, “Manda pra alguém que precisa ouvir isso”).

Finalize com uma frase que reforce a emoção ou insight do vídeo.

💡 DIRETRIZES CRIATIVAS:

O roteiro deve ser visualmente interessante e emocionalmente envolvente.

Pode sugerir locais de gravação, gestos, olhares, movimentos de câmera ou efeitos de trend.

Utilize referências de formatos populares atuais (ex: cortes rápidos, close na fala, dublagens, legendas dinâmicas).

Evite formalidade — o texto deve parecer uma conversa leve e espontânea.

Mantenha coerência com o posicionamento e voz da marca ({creator_profile_data.get('voice_tone', 'Profissional')}).

Sempre que possível, integre elementos visuais da paleta de cores ({creator_profile_data.get('color_palette', 'Não definida')}) ou ambientes que reflitam o negócio ({creator_profile_data.get('business_name', 'Não informado')}).

📦 FORMATO DE SAÍDA:

Gere o conteúdo neste formato exato:

🎬 Roteiro de Reels (20–40 segundos):

Abertura (Gancho):
[Texto curto e impactante — até 3 segundos — baseado em trend atual do nicho.]

Desenvolvimento:
[Texto fluido e natural, descrevendo falas, ações e gestos principais. Pode sugerir planos de câmera e transições visuais.]

Fechamento (CTA):
[Chamada leve e coerente com o objetivo do post. Final inspirador ou emocional.]

📅 CONTEXTO DE USO:

Este prompt será usado para gerar roteiros de Reels diários, com base no onboarding e nos dados de entrada do post.

Cada roteiro deve ser:

Original, atual e adaptado ao público do cliente;

Baseado em trends e formatos que estão performando bem no momento;

Curto, criativo e impactante o suficiente para reter atenção e gerar engajamento real;

Fiel à identidade da marca, ao tom de voz e ao estilo visual do negócio.

O resultado deve ser tão bom quanto o roteiro de um conteúdo viral profissional, pronto para ser gravado e publicado.


"""
        return prompt.strip()

    def _build_story_prompt(self, post_data: Dict) -> str:
        """Build prompt specifically for stories."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        details = post_data.get('further_details', '')

        # Get dynamic data from creator profile and post
        creator_profile_data = self._get_creator_profile_data()
        prompt = f"""
Você é um estrategista de conteúdo e roteirista criativo para redes sociais, especialista em planejar ideias de Stories envolventes, estratégicos e alinhados à marca.
Sua missão é criar 5 ideias de Stories com base nas informações do onboarding do cliente e nos dados de entrada do post.

Cada ideia deve ser prática, atual e coerente com o tema principal da campanha, respeitando a identidade visual, o tom de voz e o público da marca.


🧾 DADOS DE PERSONALIZAÇÃO DO CLIENTE:

Nome profissional: {creator_profile_data.get('professional_name', 'Não informado')}

Profissão: {creator_profile_data.get('profession', 'Não informado')}

Número de celular: {creator_profile_data.get('whatsapp_number', 'Não informado')}

Nome do negócio: {creator_profile_data.get('business_name', 'Não informado')}

Setor/Nicho: {creator_profile_data.get('specialization', 'Não informado')}

Descrição do negócio: {creator_profile_data.get('business_description', 'Não informado')}

Gênero do público-alvo: {creator_profile_data.get('target_gender', 'Não informado')}

Faixa etária do público-alvo: {creator_profile_data.get('target_age_range', 'Não informado')}

Interesses do público-alvo: {creator_profile_data.get('target_interests', 'Não informado')}

Localização do público-alvo: {creator_profile_data.get('target_location', 'Não informado')}

Logo: {creator_profile_data.get('logo', 'Não fornecido')}

Paleta de cores: {creator_profile_data.get('color_palette', 'Não definida')}

Tom de voz: {creator_profile_data.get('voice_tone', 'Profissional')}

🧠 DADOS DO POST:

Assunto: {name}

Objetivo: {objective}

Mais detalhes: {details}

OBJETIVO GERAL:

Criar 5 ideias de Stories que complementem o tema principal da campanha, mantenham o público engajado ao longo do dia e transmitam autoridade, conexão e valor.

Cada ideia deve ser simples de produzir, atual (baseada em trends do momento) e adequada ao público e nicho do cliente.

🪶 REGRAS DE CRIAÇÃO:

Conexão com o Tema Principal:

Todas as ideias devem estar relacionadas ao assunto central da campanha (definido em {name}, {objective} e {details}).

O conteúdo deve ser coerente com o post de Feed e/ou Reels do mesmo dia.

Estilo e Tom:

Adapte as ideias ao tom de voz da marca ({creator_profile_data.get('voice_tone', 'Profissional')}) e ao perfil do público ({creator_profile_data.get('target_gender', 'Não informado')}, {creator_profile_data.get('target_age_range', 'Não informado')}).

As ideias devem parecer naturais e autênticas, como se o próprio cliente estivesse falando.

Utilize linguagem leve, envolvente e humana.

Tendências:

Sempre que possível, baseie-se em trends atuais do nicho (músicas, formatos, filtros ou tipos de interação em alta).

Prefira formatos nativos de Story: enquetes, caixas de pergunta, bastidores, frases inspiradoras, vídeos curtos, depoimentos ou demonstrações.

Variedade:

Traga formatos diferentes nas 5 ideias (ex: 1 bastidor, 1 dica, 1 pergunta, 1 reflexão e 1 interação).

As ideias devem ser complementares e sequenciais, criando uma jornada de conteúdo ao longo do dia.

📦 FORMATO DE SAÍDA:

Gere a resposta neste formato exato:

📱 5 Ideias de Stories (coerentes com o tema do dia):

1️⃣ [Ideia 1 — breve descrição da ideia e sua finalidade. Ex: “Mostre um bastidor da rotina do negócio e escreva na legenda: ‘Nem sempre é fácil, mas cada passo vale a pena 💪’.”]

2️⃣ [Ideia 2 — descreva o formato (ex: enquete, pergunta, frase ou vídeo) e o tema central.]

3️⃣ [Ideia 3 — sugira uma interação simples para aumentar engajamento. Ex: “Caixa de perguntas: qual seu maior desafio com X?”]

4️⃣ [Ideia 4 — traga um insight rápido ou dica prática, que possa ser gravada em vídeo curto.]

5️⃣ [Ideia 5 — finalize o dia com algo inspirador, reflexivo ou engraçado, de acordo com o tom da marca.]

💡 EXEMPLO DE SAÍDA (tema: Saúde da Mulher):

1️⃣ Mostre um momento real do dia (ex: tomando café, indo trabalhar) e escreva: “Cuidar de si começa nos pequenos gestos ☕💗”.

2️⃣ Enquete: “Você costuma reservar um tempo só pra você?” (✅ Sim / 😅 Quase nunca).

3️⃣ Caixinha: “Qual o seu momento favorito de autocuidado?”

4️⃣ Compartilhe uma dica rápida de saúde feminina (ex: hidratação, sono, exames).

5️⃣ Finalize com uma frase trend: “Você merece se cuidar — todos os dias ✨”.

📅 CONTEXTO DE USO:

Este prompt será utilizado para gerar somente ideias de Stories diários, com base nas informações do onboarding e nos dados do post.

As ideias devem ser:

Simples e aplicáveis na rotina real do cliente;

Alinhadas às tendências visuais e comportamentais atuais;

Conectadas ao público e à essência da marca;

Diferentes a cada dia, garantindo variedade e criatividade contínua.

O resultado final deve parecer o planejamento de um estrategista de conteúdo profissional, pronto para execução imediata.

"""
        return prompt.strip()

    def _build_default_prompt(self, post_data: Dict) -> str:
        """Build default prompt for other content types (carousel, live, etc.)."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        post_type = post_data.get('type', '')
        further_details = post_data.get('further_details', '')
        include_image = post_data.get('include_image', False)

        creator_profile_section = self._get_creator_profile_section()
        additional_context = f"\n\nDetalhes Adicionais: {further_details}" if further_details and further_details.strip(
        ) else ""
        image_context = "\n\nNOTA: Uma imagem será gerada automaticamente para este post usando IA." if include_image else ""

        prompt = f"""
Você é um especialista em copywriting estratégico, criativo e persuasivo, com domínio do método AIDA (Atenção, Interesse, Desejo, Ação) e das boas práticas de comunicação digital.
Sua missão é gerar copies poderosas, relevantes e seguras para campanhas, sempre respeitando as políticas do Meta e Google Ads, evitando qualquer tipo de sensacionalismo, promessa exagerada ou afirmações que possam violar as diretrizes dessas plataformas.

### DADOS DE ENTRADA:
- Nome do Post (tema principal): {name}
- Objetivo da campanha: {objective}
- Tipo de conteúdo: {post_type} → pode ser Live, Reel, Post, Carousel ou Story
- Plataforma: instagram{creator_profile_section}{additional_context}{image_context}

### REGRAS PARA CONSTRUÇÃO DA COPY:

1. Estruture o texto internamente seguindo o método AIDA, mas **não mostre as etapas nem insira rótulos**.
   O resultado deve ser apenas o texto final, fluido e pronto para publicação.

2. A copy deve respeitar o tom de voz definido no perfil do criador (se disponível) ou usar tom profissional como padrão.

3. Respeite as políticas de publicidade do Meta e Google Ads, sem sensacionalismo, promessas exageradas ou afirmações proibidas.
   - Não usar comparações negativas diretas.
   - Não prometer resultados absolutos.
   - Não atacar autoestima ou expor dados sensíveis de forma invasiva.
   - Priorizar sempre uma comunicação positiva, inclusiva e motivadora.

4. Sempre que possível, conecte a copy com tendências e expressões atuais relacionadas ao tema.

5. **Adaptação ao Tipo de Conteúdo**
   - Se for **Post**: texto curto, envolvente e objetivo, pronto para feed.
   - Se for **Reel**: entregue um roteiro estruturado em até 15 segundos, dividido por blocos de tempo (ex.: [0s – 3s], [3s – 6s], etc.), para que a gravação siga o ritmo ideal de engajamento. A copy deve ser curta, dinâmica e clara, sempre com CTA no final.
   - Se for **Story**: copy leve, direta e conversacional, podendo ser dividida em 2 ou 3 telas curtas, incentivando interação (ex.: enquete, resposta rápida, link).
   - Se for **Carousel**: texto dividido em partes curtas que façam sentido em sequência, cada card reforçando um ponto até a CTA final.
   - Se for **Live**: copy no formato de convite, explicando tema, horário, benefício de participar e incentivo para salvar a data.

6. Ajuste o tamanho, tom e formatação da copy sempre de acordo com o tipo de conteúdo escolhido.

7. Utilize **emojis de forma estratégica e moderada** para dar leveza e proximidade ao texto, sem exageros ou excesso.

8. Faça a **separação de parágrafos de forma natural**, garantindo boa legibilidade em redes sociais e anúncios, evitando blocos de texto longos.

9. Entregue **apenas uma CTA final**, integrada ao texto, natural e clara, sem listas ou alternativas extras.

10. NÃO inclua textos explicativos, como por exemplo "Título:", "Texto:", "CTA:", ou qualquer outro rótulo.

---

### SAÍDA ESPERADA:
- Texto final pronto para ser copiado e colado.
- Copy fluida, envolvente e natural, sem divisões ou rótulos técnicos.
- Linguagem alinhada ao perfil do criador e ao tom cadastrado.
- Respeito às boas práticas do Meta e Google Ads.
- Emojis distribuídos de forma natural, sem excesso.
- Parágrafos curtos, fáceis de ler e escaneáveis.
- Uma única CTA ao final do texto.

"""
        return prompt.strip()

    def build_image_prompt(self, post_data: Dict, content: str) -> str:
        """Build the prompt for image generation based on post type."""
        post_type = post_data.get('type', '').lower()

        # Route to specific image prompt based on post type
        if post_type == 'post':
            return self._build_feed_image_prompt(post_data, content)
        elif post_type == 'reel':
            return self._build_reel_image_prompt(post_data, content)
        elif post_type == 'story':
            return self._build_story_image_prompt(post_data, content)
        else:
            # Default fallback for other types (carousel, live, etc.)
            return self._build_default_image_prompt(post_data, content)

    def _get_image_context_section(self, post_data: Dict, content: str) -> tuple:
        """Get common image context information for all image prompt types."""
        post_type = post_data.get('type', '')
        objective = post_data.get('objective', '')
        name = post_data.get('name', '')
        further_details = post_data.get('further_details', '')

        # Extract title from content if available
        title = ""
        if "Título:" in content:
            title_line = content.split("Título:")[1].split("\n")[0].strip()
            title = title_line

        # Use title from content if available, otherwise use name from post_data
        tema = title if title else name

        # Creator profile information for brand identity (if available)
        identidade_marca = "Estilo profissional e moderno"
        if hasattr(self, 'user') and self.user:
            from CreatorProfile.models import CreatorProfile
            profile = CreatorProfile.objects.filter(user=self.user).first()
            if profile:
                brand_info = []
                audience_info = []
                if profile.business_name:
                    brand_info.append(f"Empresa: {profile.business_name}")
                if profile.profession:
                    brand_info.append(f"Profissão: {profile.profession}")
                if profile.specialization:
                    brand_info.append(
                        f"Especialização: {profile.specialization}")

                # Target audience information
                if profile.target_gender and profile.target_gender.strip():
                    audience_info.append(
                        f"Gênero do Público: {profile.target_gender}")

                if profile.target_age_range and profile.target_age_range.strip():
                    audience_info.append(
                        f"Faixa Etária: {profile.target_age_range}")

                if profile.target_location and profile.target_location.strip():
                    audience_info.append(
                        f"Localização: {profile.target_location}")

                if profile.target_interests and profile.target_interests.strip():
                    audience_info.append(
                        f"Interesses: {profile.target_interests}")

                if profile.voice_tone and profile.voice_tone.strip():
                    audience_info.append(
                        f"Tom de Voz da Marca: {profile.voice_tone}")

                if audience_info:
                    brand_info.append(
                        f"Dados do Público-Alvo e Marca: {' | '.join(audience_info)}")

                # Color palette
                colors = [profile.color_1, profile.color_2,
                          profile.color_3, profile.color_4, profile.color_5]
                valid_colors = [
                    color for color in colors if color and color.strip()]
                if valid_colors:
                    brand_info.append(
                        f"Cores da marca: {', '.join(valid_colors)}")

                if brand_info:
                    identidade_marca = f"{', '.join(brand_info)}, estilo profissional"

        # Add further details context if available
        context_adicional = f" - Contexto adicional: {further_details}" if further_details and further_details.strip(
        ) else ""

        return tema, objective, post_type, identidade_marca, context_adicional

    def _build_feed_image_prompt(self, post_data: Dict, content: str) -> str:
        """Build prompt specifically for feed post images."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        further_details = post_data.get('further_details', '')

        creator_profile_data = self._get_creator_profile_data()

        # TODO: Replace with your specific feed image prompt
        prompt = f"""
Você é um diretor de arte virtual e designer premiado, especializado em criar imagens profissionais e altamente estéticas para redes sociais.
Sua missão é gerar uma imagem de excelência visual que represente, de forma criativa e coerente, o conteúdo do post de Feed produzido a partir das informações abaixo.

Essa imagem será usada como ilustração principal do post e deve parecer ter sido criada por um designer premiado e criativo, com qualidade digna de uma campanha profissional.

🧾 DADOS DE PERSONALIZAÇÃO DO CLIENTE:

Nome profissional: {creator_profile_data.get('professional_name', 'Não informado')}

Profissão: {creator_profile_data.get('profession', 'Não informado')}

Número de celular: {creator_profile_data.get('whatsapp_number', 'Não informado')}

Nome do negócio: {creator_profile_data.get('business_name', 'Não informado')}

Setor/Nicho: {creator_profile_data.get('specialization', 'Não informado')}

Descrição do negócio: {creator_profile_data.get('business_description', 'Não informado')}

Gênero do público-alvo: {creator_profile_data.get('target_gender', 'Não informado')}

Faixa etária do público-alvo: {creator_profile_data.get('target_age_range', 'Não informado')}

Interesses do público-alvo: {creator_profile_data.get('target_interests', 'Não informado')}

Localização do público-alvo: {creator_profile_data.get('target_location', 'Não informado')}

Logo: {creator_profile_data.get('logo', 'Não fornecido')}

Paleta de cores: {creator_profile_data.get('color_palette', 'Não definida')}

Tom de voz: {creator_profile_data.get('voice_tone', 'Profissional')}

🧠 DADOS DO POST:

Assunto: {name}

Objetivo: {objective}

Mais detalhes: {further_details}

OBJETIVO DA IMAGEM:

Criar uma imagem que represente visualmente o tema, emoção e intenção do post de Feed, mantendo coerência com os dados, o público e o nicho do cliente.

A imagem deve ser:

Visualmente impactante, moderna e profissional;

Autêntica e emocionalmente conectada ao público;

Com aparência de design ultra refinado, como se tivesse sido criada por um designer premiado internacionalmente;

Realista sempre que possível, utilizando pessoas reais (com expressões autênticas e emoções coerentes ao tema) quando fizer sentido;

Harmônica e fiel à paleta de cores da marca ({creator_profile_data.get('color_palette', 'Não definida')});

Alinhada às tendências visuais atuais do nicho e das redes sociais (trends em alta).

🧩 DIRETRIZES TÉCNICAS:

Tamanho: 1080 x 1350 px

Proporção: 4:5 (vertical – formato de post para Feed)

Estilo: realista, moderno e sofisticado

Qualidade: ultra-detalhada, profissional e refinada

Luz: natural e bem equilibrada (suave e inspiradora)

Textura: limpa e nítida, com foco em contraste, harmonia e composição

SEM TEXTO NA IMAGEM:

Sem marcas d’água ou elementos de interface

Pode conter pessoas reais ou elementos simbólicos relacionados ao tema, conforme adequado.

💡 ESTILO E DIREÇÃO CRIATIVA:

A imagem deve traduzir visualmente a emoção da copy.

Utilize referências visuais contemporâneas, inspiradas em campanhas de grandes marcas (ex: Apple, Nike, Natura, Heineken, Airbnb, etc.), conforme o tom da marca do cliente.

A composição deve ser inteligente e equilibrada, com atenção ao foco visual principal.

Sempre que o tema permitir, use rostos reais, olhares e gestos para transmitir empatia e conexão humana.

O resultado deve parecer fotografia ou arte de nível editorial, própria de uma campanha premiada.

📅 CONTEXTO DE USO:

Este prompt será usado para gerar apenas a imagem correspondente a um post de Feed.

A imagem deve traduzir o tema e a emoção da copy textual, respeitar a identidade visual da marca e transmitir excelência e autenticidade.

O resultado visual deve ser tão bom que pareça criado por um designer de elite, com harmonia, estilo e impacto perfeitos.

⚙️ SAÍDA OBRIGATÓRIA:

Crie uma imagem de marketing profissional e visualmente atraente, adequada para redes sociais, no formato vertical Tamanho: 1080 x 1350 px (Proporção: 4:5 (vertical – formato de post para Feed), utilizando a imagem anexada como canvas base para a arte. 

NÃO DEIXE BORDAS BRANCAS AO REDOR DA IMAGEM, PREENCHA TODO O ESPAÇO, E NEM ADICIONE TEXTOS NA IMAGEM. NÃO QUEREMOS TEXTO E NEM BORDA BRANCA, APENAS A IMAGEM NO FORMATO 4:5, 1080X1350 PX

"""
        return prompt.strip()

    def _build_reel_image_prompt(self, post_data: Dict, content: str) -> str:
        """Build prompt specifically for reel cover images."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        further_details = post_data.get('further_details', '')
        details = self._build_all_details(further_details)
        # TODO: Replace with your specific reel image prompt
        prompt = f"""
Você é um especialista em design para marketing digital e redes sociais.  
Sua missão é criar capas de Reels profissionais, modernas e impactantes, que chamem a atenção do público já no primeiro contato.  
A capa deve ser clara, objetiva e reforçar a ideia central do conteúdo, sem excesso de elementos ou textos longos.  

### DADOS DE ENTRADA:
- Assunto do post: {name}  
- Objetivo do post: {objective}  
- Tipo do post: Capa de Reel  
- Mais detalhes: {details}  

---

### REGRAS PARA A CAPA:

1. Formato: **vertical 1080x1920 px**, otimizado para Reels.  

2. A capa deve conter **uma chamada curta e impactante**, em forma de título, que incentive o clique no vídeo.  
   - Exemplo: “Energia no pós-bariátrico 💧”, “O segredo do emagrecimento saudável ✨”.  
   - Nunca usar blocos longos de texto.  

3. O design deve ser limpo, moderno e profissional, com hierarquia visual clara:  
   - Título curto em destaque.  
   - Elementos visuais que remetam ao tema.  

4. Usar **cores, tipografia e estilo compatíveis com a identidade visual da marca** (quando fornecida).  

5. Se apropriado, incluir elementos visuais sutis que conectem ao tema (ex.: gotas d’água para soroterapia, coração para saúde, ícones de energia, etc.).  

6. Evitar poluição visual e excesso de informações. A capa deve ser simples, mas altamente chamativa.  

7. Comunicação sempre ética e positiva, sem sensacionalismo ou exageros.  

8. Utilize a imagem anexada como um canvas para a geração de todas as imagens que eu te pedir. Elas devem ser criadas no formato 9:16 para serem postadas no instagram
---

### SAÍDA ESPERADA:
- **Uma imagem final no formato de capa para Reel (1080x1920 px)**.  
- O design deve conter apenas **um título curto e impactante**, sem blocos longos de texto.  
- A arte deve estar finalizada, pronta para uso como capa do Reel.  



"""
        return prompt.strip()

    def _build_story_image_prompt(self, post_data: Dict, content: str) -> str:
        """Build prompt specifically for story images."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        further_details = post_data.get('further_details', '')
        details = self._build_all_details(further_details)

        # TODO: Replace with your specific story image prompt
        prompt = f"""
Você é um especialista em design digital e marketing visual.



Sua missão é gerar uma arte de Story altamente criativa, moderna e impactante, que vá além do simples.

O resultado deve ser um design sofisticado, envolvente e visualmente atrativo, pronto para ser publicado como Story.



### DADOS DE ENTRADA (serão fornecidos pelo sistema):

- Assunto do post: {name}

- Objetivo do post: {objective}

- Tipo do post: Story

- Mais detalhes: {details}



---



### REGRAS PARA A IMAGEM:



1. Gere **apenas 1 imagem final** no formato vertical **1080x1920 px (proporção 9:16)**, otimizada para Instagram Stories.



2. Utilize a **imagem anexada como canvas base** para a geração da arte.

- As alterações devem ser feitas sobre essa base, preservando estilo, layout e identidade, a menos que outra mudança seja explicitamente pedida.



3. **Estética PREMIUM e de Vanguarda:** O design deve ter uma estética moderna, minimalista e elegante. **Implemente o 'Princípio do Espaço Negativo' (Less is More)**, utilizando hierarquia de forma sofisticada e focando na qualidade dos assets, não na quantidade. Crie profundidade com sombras suaves, gradientes bem trabalhados ou elementos 3D quando apropriado. Busque um acabamento que se assemelhe a um material de agência de alto nível (ex: FutureBrand, Pentagram).



4. **Título como ÂNCORA Visual:** Crie um título **extremamente curto** (máx. 5 palavras) e impactante, integrado ao design de forma harmoniosa, com tipografia que reflita a identidade da marca e garanta impacto imediato (tamanho e peso contrastantes).



5. **Hierarquia visual clara**:

- Título principal chamando a atenção.

- Espaço de respiro para facilitar a leitura.

- Elementos gráficos ou ilustrações de apoio que reforcem o tema (mas sem poluição visual).



6. **Coerência de Marca (Brand Guidelines):** O design deve seguir diretrizes de marca imaginárias, incluindo a paleta de cores primária e secundária, e tipografia, para garantir coesão em todas as peças. **O resultado não pode parecer genérico.**



7. **LOGOMARCA**:

- Se o cliente anexar a logomarca, **use obrigatoriamente a logo original** no design.

- Se não houver logomarca anexada, **não crie logomarca fictícia em hipótese alguma**.



8. **Imagens de pessoas reais** podem ser usadas no design para transmitir mais **profissionalismo, proximidade e autenticidade**, desde que respeitem a proposta visual da marca.



9. **Elementos Visuais de Alto Nível:** Utilize apenas **ativos visuais de alta resolução e qualidade inquestionável**. Priorize renderizações 3D abstratas, fotografia com tratamento cinematográfico, ou ilustrações vetoriais minimalistas e originais. **Evite fotos de banco de imagens genéricas.**



10. **Área de segurança (safe zone):** mantenha pelo menos 10% de margem sem textos próximos às bordas, para evitar cortes em diferentes telas.



11. Toda a comunicação visual deve ser **positiva, ética e inspiradora**, sem sensacionalismo ou exageros.



12. **Regras de texto em PT-BR (Blindagem Total Contra Erros):**



12.1. Criação e Validação por Redundância:

- A IA deve criar a copy curta e impactante **exclusivamente em Português do Brasil (pt-BR)**.

- **PROTOCOLO DE REVISÃO DUPLA:** 1º - Rascunho: Gere a copy inicial. 2º - Validação Rigorosa: Submeta esta copy a uma revisão gramatical e ortográfica automática de nível avançado. O resultado **FINAL** deve ser zero erros de ortografia, acentuação ou concordância.



12.2. Lista de Checagem (Checklist) Ortográfica e Gramatical Essencial:

- A IA deve confirmar o seguinte com **extremo rigor** antes de finalizar a imagem:

- **100% de Correção Ortográfica:** Cada palavra individualmente deve ser verificada para garantir sua grafia exata e correta em PT-BR. **Nenhum erro de digitação (typo), troca de letras, inversão, omissão ou adição de letras é permitido em hipótese alguma** (ex: "Garanitad" é proibido, deve ser "Garantida").

- **Acentos:** Todas as palavras essenciais (ex: saúde, médico, física) e de regra geral estão acentuadas corretamente.

- **Crase:** O uso de crase foi validado.

- **Concordância:** A concordância nominal e verbal está perfeita.

- **Validação Lexical:** Cada palavra utilizada deve ser **validada ativamente por sua existência e grafia correta em um dicionário de Português do Brasil padrão**, assegurando que não há palavras inventadas ou corrompidas.



12.3. Aplicação Técnica:

- Renderizar os textos como camadas de texto editável (live text) usando tipografia que suporte totalmente os caracteres pt-BR (ex.: Inter, Montserrat, Poppins, Nunito, Roboto).

- Garantir alta legibilidade: contraste adequado, sem distorção, sem warp, espaçamento e acentuação preservados.

- Validação Final: A IA deve validar internamente que todas as palavras estão corretas em pt-BR antes da renderização final.



---



### SAÍDA ESPERADA:

- **Uma única imagem final premium em formato 1080x1920 px (9:16)**.

- Arte com acabamento visual sofisticado, criativo e impactante, pronta para Story.

- Design moderno, com chamada curta em destaque e alinhado ao tema do post.

- Estética de alto nível, como um material produzido em agência de design profissional.

- Logomarca usada apenas se fornecida, nunca criada artificialmente.

- Possibilidade de incluir **pessoas reais** no design para transmitir mais profissionalismo e autenticidade.

- Texto criado pela IA em **pt-BR perfeito**, sem erros de português, pronto para publicação.
"""
        return prompt.strip()

    def _build_default_image_prompt(self, post_data: Dict, content: str) -> str:
        """Build default prompt for other image types (carousel, live, etc.)."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        further_details = post_data.get('further_details', '')
        details = self._build_all_details(further_details)
        prompt = f"""Você é um especialista em criação visual para marketing digital e redes sociais.  
Sua missão é gerar imagens criativas, profissionais e impactantes que transmitam a mensagem central da campanha.  

### DADOS DE ENTRADA (serão fornecidos pelo sistema):
- Assunto do post: {name}
- Objetivo do post: {objective}
- Tipo do post: Story ou feed ou reels
- Mais detalhes: {details}

---

### REGRAS PARA GERAÇÃO DA IMAGEM:

1. A imagem deve ser **clara, atrativa e coerente** com o tema central e o objetivo da campanha.  
2. Ajustar o **formato da arte** conforme o tipo de conteúdo (ex.: Story 1080x1920, Post 1080x1080, Reel capa 1080x1920).  
3. Representar a mensagem de forma **ética e respeitosa**, sem estereótipos ou sensacionalismo.  
4. Usar elementos visuais que conectem com o **perfil do criador e sua área de atuação**.  
5. Se houver informações da empresa (logo, paleta de cores, estilo visual), elas devem ser integradas.  
6. Evite excesso de texto. Se for necessário, use frases curtas e legíveis.  
7. A imagem deve parecer **profissional e de alta qualidade**, pronta para publicação em redes sociais.  

---

### SAÍDA ESPERADA:
- A imagem, em alta qualidade, compreendendo todas as informações passadas"""

        return prompt.strip()

    def build_regeneration_prompt(self, current_content: str, user_prompt: str) -> str:
        """Build the prompt for content regeneration with user feedback."""

        prompt = f"""
Você é um especialista em ajustes e refinamentos de conteúdo para marketing digital.  
Sua missão é editar o material já criado (copy) mantendo sua identidade visual, estilo e tom, alterando **apenas o que for solicitado**.  

### DADOS DE ENTRADA:
- Conteúdo original: {current_content}  
- Alterações solicitadas: {user_prompt}

---

### REGRAS PARA EDIÇÃO:

1. **Mantenha toda a identidade visual e estilística do conteúdo original**:  
   - Paleta de cores  
   - Tipografia  
   - Layout  
   - Tom de voz e estilo da copy  
   - Estrutura do design ou texto  

2. **Modifique somente o que foi solicitado** pelo profissional, sem alterar nada além disso.  

3. Ajuste apenas as frases, palavras ou CTA especificadas, mantendo a mesma estrutura, tom e parágrafos curtos.  

4. Nunca descaracterize o material já feito. A ideia é **refinar e ajustar**, não recriar.  

5. O resultado deve estar pronto para uso imediato, atualizado conforme solicitado e sem perda da identidade visual/marca.  

---

### SAÍDA ESPERADA:
- Versão revisada do conteúdo (copy), com **as alterações solicitadas aplicadas**.  
- Todo o restante deve permanecer idêntico ao original.  
- Material final pronto para publicação.  

"""

        return prompt

    def build_variation_prompt(self, current_content: str) -> str:
        """Build the prompt for creating a variation of existing content."""
        prompt = f"""
Você é um especialista em ajustes e refinamentos de conteúdo para marketing digital.  
Sua missão é editar o material já criado (copy) mantendo sua identidade visual, estilo e tom, alterando **apenas o que for solicitado**.  

### DADOS DE ENTRADA:
- Conteúdo original: {current_content}  

---

### REGRAS PARA EDIÇÃO:

1. **Mantenha toda a identidade visual e estilística do conteúdo original**:  
   - Paleta de cores  
   - Tipografia  
   - Layout  
   - Tom de voz e estilo da copy  
   - Estrutura do design ou texto  

2. **Modifique somente o que foi solicitado** pelo profissional, sem alterar nada além disso.  

3. Ajuste apenas as frases, palavras ou CTA especificadas, mantendo a mesma estrutura, tom e parágrafos curtos.  

4. Nunca descaracterize o material já feito. A ideia é **refinar e ajustar**, não recriar.  

5. O resultado deve estar pronto para uso imediato, atualizado conforme solicitado e sem perda da identidade visual/marca.  

---

### SAÍDA ESPERADA:
- Versão revisada do conteúdo (copy), com **as alterações solicitadas aplicadas**.  
- Todo o restante deve permanecer idêntico ao original.  
- Material final pronto para publicação.  


"""

        return prompt

    def build_image_regeneration_prompt(self, user_prompt: str) -> str:
        """Build the prompt for image regeneration with user feedback."""

        # If no current image is found, we need to create a new image based on the user's request
        prompt = f"""
Você é um especialista em design digital e edição de imagens para marketing.  
Sua missão é editar a imagem já criada, mantendo **100% da identidade visual, layout, estilo, cores e elementos originais**, alterando **apenas o que for solicitado**.  

### DADOS DE ENTRADA:
- Imagem original: [IMAGEM ANEXADA]
- Alterações solicitadas: {user_prompt if user_prompt else 'imagem parecida mas diferente, dê-me uma nova versão'}

---

### REGRAS PARA EDIÇÃO:

1. **Nunca recrie a imagem do zero.**  
   - O design, estilo, paleta de cores, tipografia, elementos gráficos e identidade visual devem permanecer exatamente iguais à arte original.  

2. **Aplique apenas as mudanças solicitadas.**  
   - Exemplo: se o pedido for “mudar o título para X”, altere somente o texto do título, mantendo a fonte, cor, tamanho e posicionamento original.  
   - Se o pedido for “trocar a cor do fundo”, altere apenas essa cor, mantendo todos os demais elementos intactos.  

3. **Não adicione novos elementos** que não foram solicitados.  
   - O layout deve permanecer idêntico.  

4. **Respeite sempre a logomarca oficial** caso já esteja aplicada na arte.  

5. O resultado deve parecer exatamente a mesma imagem original, com apenas os pontos ajustados conforme solicitado.  

---

### SAÍDA ESPERADA:
- **A mesma imagem original, com apenas as alterações solicitadas aplicadas.**  
- Nada além do que foi pedido deve ser modificado.  
- O design final deve estar pronto para uso, fiel ao original.  



"""

        return prompt

    def _build_automatic_post_prompt(self, post_data: Dict, creator_profile_data: Dict) -> str:
        """Build prompt for automatic post creation based on creator profile."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        further_details = post_data.get('further_details', '')

        prompt = f"""
     Você é um estrategista criativo especializado em copywriting e conteúdo digital, responsável por garantir que cada nova campanha gerada mantenha qualidade, coerência e originalidade absoluta.
Sua função é analisar o histórico de conteúdos anteriores, entender o estilo, linguagem e temas já abordados, e criar um novo direcionamento criativo inédito, mantendo todas as regras, estrutura e padrão definidos no Prompt Mestre.
O resultado deve ser obrigatoriamente retornado no formato JSON descrito no final deste prompt.

🧾 DADOS DE PERSONALIZAÇÃO DO CLIENTE:

Nome profissional: {creator_profile_data.get('professional_name', '')}

Profissão: {creator_profile_data.get('profession', '')}

Número de celular: {creator_profile_data.get('whatsapp_number', '')}

Nome do negócio: {creator_profile_data.get('business_name', '')}

Setor/Nicho: {creator_profile_data.get('specialization', '')}

Descrição do negócio: {creator_profile_data.get('business_description', '')}

Gênero do público-alvo: {creator_profile_data.get('target_gender', '')}

Faixa etária do público-alvo: {creator_profile_data.get('target_age_range', '')}

Interesses do público-alvo: {creator_profile_data.get('target_interests', '')}

Localização do público-alvo: {creator_profile_data.get('target_location', '')}

Logo: {creator_profile_data.get('logo', '')}

Paleta de cores: {creator_profile_data.get('color_palette', '')}

Tom de voz: {creator_profile_data.get('voice_tone', '')}

🧠 DADOS DO POST ATUAL:
Assunto: {name}


Objetivo: {objective}


Mais detalhes: {further_details}

🎯 OBJETIVO DO PROMPT:
A partir do histórico recebido, sua missão é:
Analisar profundamente o conteúdo anterior, identificando:


Temas, ganchos e ideias já utilizados;


Frases, CTAs, estruturas e estilos de escrita repetidos;


Padrões visuais ou emocionais frequentes.


Evitar qualquer repetição, garantindo que o novo conteúdo:


Seja 100% original, com vocabulário, abordagem e emoção renovados;


Explore novos ângulos e gatilhos dentro do mesmo tema;


Traga novas referências, analogias ou expressões;


Use CTAs e títulos inéditos, sem reaproveitar os anteriores.


Manter o contexto da campanha, ou seja:


O novo conteúdo deve seguir o mesmo propósito, objetivo e linha narrativa;


Deve refletir o mesmo posicionamento, público e tom de voz;


Mas apresentar novas ideias e abordagens, com frescor e autenticidade.



🪶 DIRETRIZES DE ESTILO:
Mantenha todas as regras, estrutura e padrões de qualidade do Prompt Mestre.


Preserve o tom de voz da marca ({creator_profile_data.get('voice_tone', '')}) e o perfil do público.


Busque inovação criativa dentro do mesmo contexto — sem descaracterizar o estilo.


Se inspire em novas tendências atuais do nicho ({creator_profile_data.get('specialization', '')}) e expressões recentes nas redes.


A ideia deve parecer nova e empolgante, sem soar genérica ou repetitiva.



⚙️ FORMATO DE SAÍDA (OBRIGATÓRIO):
A resposta deve ser entregue estritamente em formato JSON, seguindo exatamente esta estrutura:
{
            "historical_analysis": "",
  "avoid_list": [],
  "new_direction": "",
  "new_headline": "",
  "new_subtitle": "",
  "new_cta": ""
}

⚙️ Regras de preenchimento do JSON:
historical_analysis: breve análise do histórico, destacando o que foi mais usado (ganchos, CTAs, temas e padrões).


avoid_list: lista com expressões, ideias ou CTAs que não devem ser repetidas.


new_direction: resumo da nova linha criativa (novo enfoque, emoção, narrativa e ângulo de comunicação).


new_headline: novo título curto e original (até 8 palavras, diferente de qualquer anterior).


new_subtitle: subtítulo complementar, criativo e inédito.


new_cta: chamada clara, natural e diferente das anteriores.



📅 CONTEXTO DE USO:
Este prompt será executado antes do Prompt Mestre em cada geração diária.
Ele serve como filtro criativo e analítico, garantindo que o novo conteúdo:
Não repita nenhuma parte do histórico;


Se mantenha totalmente original e contextualmente coerente;


Siga todas as regras do Prompt Mestre (estrutura AIDA, tom, tendências, proibições e qualidade visual);


E entregue uma nova linha de raciocínio para o próximo conteúdo da campanha.


        """
        return prompt.strip()
