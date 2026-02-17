import logging
import random
from typing import Dict, List

from CreatorProfile.models import CreatorProfile, VisualStylePreference

# Logger para o serviço de prompts
logger = logging.getLogger(__name__)


# Mapeamento de cores HEX para descrições narrativas
HEX_TO_COLOR_NAME = {
    '#8B5CF6': 'Roxo vibrante',
    '#FFFFFF': 'Branco puro',
    '#4B4646': 'Cinza carvão escuro',
    '#A855F7': 'Violeta claro',
    '#EC4899': 'Rosa magenta',
    '#000000': 'Preto',
    '#F5F5F5': 'Cinza claro',
    '#333333': 'Cinza escuro',
    '#FF6B6B': 'Vermelho coral',
    '#4ECDC4': 'Verde água',
    '#FFE66D': 'Amarelo dourado',
    '#95E1D3': 'Verde menta',
    '#F38181': 'Rosa salmão',
    '#AA96DA': 'Lavanda',
    '#FCBAD3': 'Rosa claro',
    '#FFFFD2': 'Creme',
}


def _format_colors_for_logo(color_palette: List[str]) -> str:
    """
    Converte lista de cores HEX para descrição narrativa.

    Usado nos prompts de logo para evitar que a IA renderize
    os códigos HEX como swatches ou blocos de cor.

    Args:
        color_palette: Lista de cores HEX (ex: ['#8B5CF6', '#FFFFFF'])

    Returns:
        String com descrições narrativas das cores, uma por linha
    """
    if not color_palette:
        return "- Cores não definidas"

    descriptions = []
    for hex_color in color_palette:
        hex_upper = hex_color.upper() if hex_color else ''
        name = HEX_TO_COLOR_NAME.get(hex_upper, f'Cor personalizada ({hex_color})')
        descriptions.append(f"- {name}")

    return "\n".join(descriptions)


def _build_logo_prompt_section(
    business_name: str,
    color_palette: List[str],
    position: str = "bottom-right corner"
) -> str:
    """
    Gera a seção de prompt estruturado para a logo da marca.

    Esta função centraliza todas as regras necessárias para preservar
    a logo corretamente durante a geração de imagens, usando as cores
    do onboarding para flexibilidade de adaptação.

    Segue as melhores práticas de prompt engineering para image-to-image:
    - Narrativa descritiva (não bullets)
    - Reconhecimento explícito da imagem anexada
    - Diretivas de preservação específicas
    - Instrução "change only X, keep everything else"
    - Sem instruções negativas

    Args:
        business_name: Nome da marca (ex: "Postnow")
        color_palette: Lista de cores HEX do onboarding
        position: Posição desejada na imagem (default: bottom-right corner)

    Returns:
        String formatada com instruções completas para a logo
    """
    cores_formatadas = _format_colors_for_logo(color_palette)

    return f"""
**LOGO (Preserved Element):**

Using the attached logo image of "{business_name}", place it in the {position} at approximately 8% of the image width, ensuring it remains clearly visible but not dominant.

PRESERVE EXACTLY: the icon shape and geometry, the text "{business_name}" spelling and arrangement, and the overall logo proportions. The logo must appear exactly as provided in the attachment.

Change ONLY the logo colors if needed for contrast against the background. Choose from the brand palette colors that provide maximum readability:
{cores_formatadas}

Keep the logo unchanged in every other aspect: same icon geometry, same text content, same layout structure. Ensure all parts of the logo are fully visible and legible against any background color.
""".strip()


class PromptService:
    def __init__(self):
        self.user = None

    def set_user(self, user):
        """Set the user for this PromptService instance."""
        self.user = user

    def _get_random_visual_style(self, profile) -> dict:
        """Randomly select a visual style from user's visual_style_ids.

        Returns a dict with 'name' and 'description' for structured prompt building.
        """
        if not profile.visual_style_ids or len(profile.visual_style_ids) == 0:
            return {"name": "", "description": ""}

        random_style_id = random.choice(profile.visual_style_ids)
        try:
            visual_style = VisualStylePreference.objects.get(id=random_style_id)
            return {
                "name": visual_style.name,
                "description": visual_style.description
            }
        except VisualStylePreference.DoesNotExist:
            return {"name": "", "description": ""}

    def _format_creator_profile_section(self, profile_data: Dict, include_phone: bool = False) -> str:
        """
        Formata a seção de dados do creator profile para uso em prompts.

        Centraliza a formatação para evitar duplicação em múltiplos prompts.

        Args:
            profile_data: Dicionário com dados do perfil (de get_creator_profile_data)
            include_phone: Se True, inclui o telefone do negócio

        Returns:
            String formatada com os dados do perfil
        """
        sections = [
            f"Nome do negócio: {profile_data.get('business_name', 'Não informado')}",
        ]

        if include_phone:
            sections.append(f"Telefone do negócio: {profile_data.get('business_phone', 'Não informado')}")

        sections.extend([
            f"Setor/Nicho: {profile_data.get('specialization', 'Não informado')}",
            f"Descrição do negócio: {profile_data.get('business_description', 'Não informado')}",
            f"Público-alvo: {profile_data.get('target_audience', 'Não informado')}",
            f"Interesses do público-alvo: {profile_data.get('target_interests', 'Não informado')}",
            f"Localização do negócio: {profile_data.get('business_location', 'Não informado')}",
            f"Paleta de cores: {profile_data.get('color_palette', 'Não definida')}",
            f"Tom de voz: {profile_data.get('voice_tone', 'Profissional')}",
        ])

        return "\n\n".join(sections)

    def _format_post_data_section(self, post_data: Dict) -> str:
        """
        Formata a seção de dados do post para uso em prompts.

        Args:
            post_data: Dicionário com dados do post

        Returns:
            String formatada com os dados do post
        """
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        details = post_data.get('further_details', '')

        return f"""Assunto: {name}

Objetivo: {objective}

Mais detalhes: {details if details else 'Nenhum'}"""

    def build_content_prompt(self, post_data: Dict) -> str:
        """Build the prompt for content generation based on post type."""
        post_type = post_data.get('type', '').lower()
        post_name = post_data.get('name', 'unnamed')

        logger.info(f"Building content prompt: type={post_type}, name={post_name}")

        # Route to specific prompt based on post type
        if post_type == 'post':
            result = self._build_feed_post_prompt(post_data)
            logger.debug(f"Built feed post prompt ({len(result)} chars)")
            return result
        elif post_type == 'reel':
            result = self._build_reel_prompt(post_data)
            logger.debug(f"Built reel prompt ({len(result)} chars)")
            return result
        elif post_type == 'story':
            result = self._build_story_prompt(post_data)
            logger.debug(f"Built story prompt ({len(result)} chars)")
            return result
        elif post_type == 'campaign':
            result = self.build_automatic_post_prompt(None)
            logger.debug(f"Built campaign prompt ({len(result)} chars)")
            return result

        logger.warning(f"Unknown post type: {post_type}")
        return ""

    def get_creator_profile_data(self) -> dict:
        """Fetch and return the creator profile data for the current user."""
        if not self.user:
            logger.error("Attempted to get creator profile data without setting user")
            raise ValueError(
                "User is not set for PromptService. Call set_user(user) first or pass user parameter when creating prompts.")

        try:
            profile = CreatorProfile.objects.get(user=self.user)
            logger.debug(f"Loaded CreatorProfile for user {self.user.id}: {profile.business_name}")
        except CreatorProfile.DoesNotExist:
            logger.warning(f"CreatorProfile not found for user {self.user.id if hasattr(self.user, 'id') else 'unknown'}")
            raise ValueError(
                f"CreatorProfile not found for user {self.user.id if hasattr(self.user, 'id') else 'unknown'}")
        profile_data = {
            "business_name": profile.business_name,
            "business_phone": profile.business_phone,
            "business_website": profile.business_website,
            "business_instagram_handle": profile.business_instagram_handle,
            "specialization": profile.specialization,
            "business_description": profile.business_description,
            "business_purpose": profile.business_purpose,
            "brand_personality": profile.brand_personality,
            "products_services": profile.products_services,
            "business_location": profile.business_location,
            "target_audience": profile.target_audience,
            "target_interests": profile.target_interests,
            "main_competitors": profile.main_competitors,
            "reference_profiles": profile.reference_profiles,
            "voice_tone": profile.voice_tone,
            "visual_style": self._get_random_visual_style(profile),
            'color_palette': [color for color in [
                profile.color_1, profile.color_2,
                profile.color_3, profile.color_4, profile.color_5
            ] if color],
        }
        return profile_data

    def _build_feed_post_prompt(self, post_data: Dict) -> str:
        """Build prompt specifically for feed posts."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        details = post_data.get('further_details', '')

        # Get dynamic data from creator profile and post
        creator_profile_data = self.get_creator_profile_data()

        prompt = f"""
Você é um especialista em copywriting estratégico, criativo e persuasivo, com foco em posts de Feed para redes sociais (Instagram, Facebook, LinkedIn, etc.).

Sua missão é gerar posts de Feed completos, com base nos dados do onboarding do cliente e nos dados de entrada abaixo.

O texto deve ser fluido, natural, relevante e alinhado às tendências atuais do nicho, utilizando o método AIDA e linguagem adaptada ao público.

🧾 DADOS DE PERSONALIZAÇÃO DO CLIENTE:


Nome do negócio: {creator_profile_data.get('business_name', 'Não informado')}

Setor/Nicho: {creator_profile_data.get('specialization', 'Não informado')}

Descrição do negócio: {creator_profile_data.get('business_description', 'Não informado')}

Interesses do público-alvo: {creator_profile_data.get('target_interests', 'Não informado')}

Paleta de cores: {creator_profile_data.get('color_palette', 'Não definida')}

Tom de voz: {creator_profile_data.get('voice_tone', 'Profissional')}

🧠 DADOS DO POST:

Assunto: {name}

Objetivo: {objective}

Mais detalhes: {details}

🎯 OBJETIVO GERAL:

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

Adapte a linguagem ao público-alvo ({creator_profile_data.get('target_audience', 'Não informado')}) e localização ({creator_profile_data.get('business_location', 'Não informado')}).

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

        creator_profile_data = self.get_creator_profile_data()
        # TODO: Replace with your specific reel prompt
        prompt = f"""
Você é um roteirista criativo e estrategista de conteúdo digital, especialista em roteiros curtos e envolventes para Reels.
Sua missão é criar roteiros personalizados de 20 a 40 segundos, com base nas informações do onboarding do cliente e nos dados de entrada do post.

O roteiro deve ser atual, estratégico, dinâmico e conectado às tendências do momento dentro do nicho do cliente.

 DADOS DE PERSONALIZAÇÃO DO CLIENTE:

Nome do negócio: {creator_profile_data.get('business_name', 'Não informado')}

Telefone do negócio: {creator_profile_data.get('business_phone', 'Não informado')}

Setor/Nicho: {creator_profile_data.get('specialization', 'Não informado')}

Descrição do negócio: {creator_profile_data.get('business_description', 'Não informado')}

Público-alvo: {creator_profile_data.get('target_audience', 'Não informado')}

Interesses do público-alvo: {creator_profile_data.get('target_interests', 'Não informado')}

Localização do negócio: {creator_profile_data.get('business_location', 'Não informado')}

Paleta de cores: {creator_profile_data.get('color_palette', 'Não definida')}

Tom de voz: {creator_profile_data.get('voice_tone', 'Profissional')}

🧠 DADOS DO POST:

Assunto: {name}

Objetivo: {objective}

Mais detalhes: {details}

🎯 OBJETIVO DO ROTEIRO:

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
        creator_profile_data = self.get_creator_profile_data()
        prompt = f"""
Você é um estrategista de conteúdo e roteirista criativo para redes sociais, especialista em planejar ideias de Stories envolventes, estratégicos e alinhados à marca.
Sua missão é criar 5 ideias de Stories com base nas informações do onboarding do cliente e nos dados de entrada do post.

Cada ideia deve ser prática, atual e coerente com o tema principal da campanha, respeitando a identidade visual, o tom de voz e o público da marca.

🧾 DADOS DE PERSONALIZAÇÃO DO CLIENTE:

Nome do negócio: {creator_profile_data.get('business_name', 'Não informado')}

Telefone do negócio: {creator_profile_data.get('business_phone', 'Não informado')}

Setor/Nicho: {creator_profile_data.get('specialization', 'Não informado')}

Descrição do negócio: {creator_profile_data.get('business_description', 'Não informado')}

Público-alvo: {creator_profile_data.get('target_audience', 'Não informado')}

Interesses do público-alvo: {creator_profile_data.get('target_interests', 'Não informado')}

Localização do negócio: {creator_profile_data.get('business_location', 'Não informado')}

Paleta de cores: {creator_profile_data.get('color_palette', 'Não definida')}

Tom de voz: {creator_profile_data.get('voice_tone', 'Profissional')}

🧠 DADOS DO POST:

Assunto: {name}

Objetivo: {objective}

Mais detalhes: {details}

🎯 OBJETIVO GERAL:

Criar 5 ideias de Stories que complementem o tema principal da campanha, mantenham o público engajado ao longo do dia e transmitam autoridade, conexão e valor.

Cada ideia deve ser simples de produzir, atual (baseada em trends do momento) e adequada ao público e nicho do cliente.

🪶 REGRAS DE CRIAÇÃO:

Conexão com o Tema Principal:

Todas as ideias devem estar relacionadas ao assunto central da campanha (definido em {name}, {objective} e {details}).

O conteúdo deve ser coerente com o post de Feed e/ou Reels do mesmo dia.

Estilo e Tom:

Adapte as ideias ao tom de voz da marca ({creator_profile_data.get('voice_tone', 'Profissional')}) e ao perfil do público ({creator_profile_data.get('target_audience', 'Não informado')}).

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

⿡ [Ideia 1 — breve descrição da ideia e sua finalidade. Ex: “Mostre um bastidor da rotina do negócio e escreva na legenda: ‘Nem sempre é fácil, mas cada passo vale a pena 💪’.”]

⿢ [Ideia 2 — descreva o formato (ex: enquete, pergunta, frase ou vídeo) e o tema central.]

⿣ [Ideia 3 — sugira uma interação simples para aumentar engajamento. Ex: “Caixa de perguntas: qual seu maior desafio com X?”]

⿤ [Ideia 4 — traga um insight rápido ou dica prática, que possa ser gravada em vídeo curto.]

⿥ [Ideia 5 — finalize o dia com algo inspirador, reflexivo ou engraçado, de acordo com o tom da marca.]

💡 EXEMPLO DE SAÍDA (tema: Saúde da Mulher):

⿡ Mostre um momento real do dia (ex: tomando café, indo trabalhar) e escreva: “Cuidar de si começa nos pequenos gestos ☕💗”.

⿢ Enquete: “Você costuma reservar um tempo só pra você?” (✅ Sim / 😅 Quase nunca).

⿣ Caixinha: “Qual o seu momento favorito de autocuidado?”

⿤ Compartilhe uma dica rápida de saúde feminina (ex: hidratação, sono, exames).

⿥ Finalize com uma frase trend: “Você merece se cuidar — todos os dias ✨”.

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

    def build_image_prompt(self, post_data: Dict, content: str) -> str:
        """Build the prompt for image generation based on post type."""
        post_type = post_data.get('type', '').lower()
        post_name = post_data.get('name', 'unnamed')

        logger.info(f"Building image prompt: type={post_type}, name={post_name}")

        # Route to specific image prompt based on post type
        if post_type == 'post':
            result = self._build_feed_image_prompt(post_data, content)
            logger.debug(f"Built feed image prompt ({len(result)} chars)")
            return result
        elif post_type == 'reel':
            result = self._build_reel_image_prompt(post_data, content)
            logger.debug(f"Built reel image prompt ({len(result)} chars)")
            return result
        elif post_type == 'story':
            result = self._build_story_image_prompt(post_data, content)
            logger.debug(f"Built story image prompt ({len(result)} chars)")
            return result

        logger.warning(f"Unknown post type for image prompt: {post_type}")
        return ""

    def _format_color_palette(self, colors: list) -> str:
        """Format color palette for prompt display."""
        if not colors:
            return "Não definida"
        return ", ".join(colors)

    def _build_feed_image_prompt(self, post_data: Dict, content: str) -> str:
        """Build prompt specifically for feed post images using structured format."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        further_details = post_data.get('further_details', '')

        creator_profile_data = self.get_creator_profile_data()
        visual_style = creator_profile_data.get('visual_style', {})
        visual_style_name = visual_style.get('name', '') if isinstance(visual_style, dict) else ''
        visual_style_description = visual_style.get('description', '') if isinstance(visual_style, dict) else ''
        color_palette = self._format_color_palette(creator_profile_data.get('color_palette', []))

        prompt = f"""
### PERSONA ###
Você é um diretor de arte premiado internacionalmente, com 15 anos de experiência criando campanhas visuais para marcas como Apple, Nike e Airbnb. Especialista em design para redes sociais, você domina composição, teoria das cores e tendências visuais contemporâneas.

---

### CONTEXTO ###
Você está criando uma imagem para o Instagram de "{creator_profile_data.get('business_name', 'Não informado')}".

**Dados do Negócio:**
- Nicho/Setor: {creator_profile_data.get('specialization', 'Não informado')}
- Descrição: {creator_profile_data.get('business_description', 'Não informado')}
- Localização: {creator_profile_data.get('business_location', 'Não informado')}
- Tom de voz da marca: {creator_profile_data.get('voice_tone', 'Profissional')}

**Público-Alvo:**
- Perfil: {creator_profile_data.get('target_audience', 'Não informado')}
- Interesses: {creator_profile_data.get('target_interests', 'Não informado')}

**Identidade Visual da Marca:**
- Paleta de cores: {color_palette}

**Dados do Post:**
- Assunto: {name}
- Objetivo: {objective}
- Detalhes adicionais: {further_details if further_details else 'Nenhum'}

---

### TAREFA ###
Crie uma imagem de post para Feed do Instagram que:
1. Transmita visualmente o tema "{name}" de forma impactante
2. Conecte emocionalmente com o público-alvo
3. Reflita a identidade e valores da marca
4. Pareça criada por uma agência de design de alto nível

---

### ESTILO VISUAL OBRIGATÓRIO: {visual_style_name if visual_style_name else 'Profissional Moderno'} ###
{visual_style_description if visual_style_description else 'Design profissional, moderno e sofisticado. Composição equilibrada com foco visual claro. Cores harmônicas e iluminação natural. Estética contemporânea adequada para redes sociais.'}

---

### DIRETRIZES TÉCNICAS ###
- **Formato:** 1080 x 1350 px (proporção 4:5 vertical)
- **Qualidade:** Ultra-detalhada, renderização profissional
- **Iluminação:** Natural, suave e bem equilibrada
- **Composição:** Equilibrada, com hierarquia visual clara
- **Cores:** Usar OBRIGATORIAMENTE a paleta da marca: {color_palette}

---

### RESTRIÇÕES (O QUE EVITAR) ###
- Evitar marcas d'água ou elementos de interface
- Evitar textos longos ou ilegíveis na imagem
- Evitar clichês visuais genéricos
- Evitar poluição visual ou excesso de elementos
- Evitar cores fora da paleta da marca
- Evitar imagens que pareçam de banco de imagens genérico

---

{_build_logo_prompt_section(
    business_name=creator_profile_data.get('business_name', 'Marca'),
    color_palette=creator_profile_data.get('color_palette', [])
)}

---

### FORMATO DE SAÍDA ###
Gere uma descrição detalhada da imagem ideal (60-100 palavras) que será passada diretamente para o gerador de imagens. A descrição deve incluir:
- Elementos visuais principais
- Atmosfera e mood
- Cores predominantes (da paleta da marca)
- Estilo de iluminação
- Composição e enquadramento

**Exemplo de saída:**
"Mulher sorrindo em ambiente minimalista com luz natural suave. Fundo em tons de {color_palette}. Composição vertical 4:5, estilo editorial premium. Elementos sutis relacionados a [nicho]. Atmosfera profissional e acolhedora. Qualidade de fotografia de revista."

---

### INSTRUÇÃO FINAL ###
Utilize a imagem anexada como canvas base. Crie uma arte profissional no formato 1080 x 1350 px, pronta para publicação no Feed do Instagram.
"""
        return prompt.strip()

    def _build_reel_image_prompt(self, post_data: Dict, content: str) -> str:
        """Build prompt specifically for reel cover images using structured format."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        further_details = post_data.get('further_details', '')

        creator_profile_data = self.get_creator_profile_data()
        visual_style = creator_profile_data.get('visual_style', {})
        visual_style_name = visual_style.get('name', '') if isinstance(visual_style, dict) else ''
        visual_style_description = visual_style.get('description', '') if isinstance(visual_style, dict) else ''
        color_palette = self._format_color_palette(creator_profile_data.get('color_palette', []))

        prompt = f"""
### PERSONA ###
Você é um designer especialista em thumbnails e capas de Reels virais, com experiência comprovada em criar capas que aumentam a taxa de cliques em 300%. Você domina as tendências visuais do Instagram e sabe exatamente o que faz o público parar de rolar o feed.

---

### CONTEXTO ###
Você está criando uma capa de Reel para "{creator_profile_data.get('business_name', 'Não informado')}".

**Dados do Negócio:**
- Nicho/Setor: {creator_profile_data.get('specialization', 'Não informado')}
- Tom de voz da marca: {creator_profile_data.get('voice_tone', 'Profissional')}

**Público-Alvo:**
- Perfil: {creator_profile_data.get('target_audience', 'Não informado')}

**Identidade Visual:**
- Paleta de cores: {color_palette}

**Dados do Reel:**
- Assunto: {name}
- Objetivo: {objective}
- Detalhes: {further_details if further_details else 'Nenhum'}

---

### TAREFA ###
Crie uma capa de Reel que:
1. Capture a atenção nos primeiros 0.5 segundos
2. Comunique claramente o tema do vídeo
3. Incentive o clique com curiosidade ou valor prometido
4. Reflita a identidade visual da marca

---

### ESTILO VISUAL OBRIGATÓRIO: {visual_style_name if visual_style_name else 'Moderno e Impactante'} ###
{visual_style_description if visual_style_description else 'Design moderno e impactante. Título curto em destaque. Composição limpa com hierarquia visual clara. Cores vibrantes mas harmônicas.'}

---

### DIRETRIZES TÉCNICAS ###
- **Formato:** 1080 x 1920 px (proporção 9:16 vertical)
- **Título:** Máximo 5-7 palavras, fonte bold e legível
- **Composição:** Título em destaque (30% superior ou central)
- **Cores:** OBRIGATÓRIO usar paleta da marca: {color_palette}
- **Tipografia:** Bold, alto contraste, fácil leitura em mobile

---

### RESTRIÇÕES (O QUE EVITAR) ###
- Evitar blocos longos de texto
- Evitar fontes finas ou difíceis de ler
- Evitar poluição visual
- Evitar cores fora da paleta da marca
- Evitar imagens genéricas de banco
- Evitar sensacionalismo ou clickbait exagerado

---

{_build_logo_prompt_section(
    business_name=creator_profile_data.get('business_name', 'Marca'),
    color_palette=creator_profile_data.get('color_palette', [])
)}

---

### EXEMPLOS DE TÍTULOS EFICAZES ###
- "3 erros que você comete"
- "O segredo que ninguém conta"
- "Pare de fazer isso agora"
- "Como [resultado] em [tempo]"

---

### FORMATO DE SAÍDA ###
Gere uma descrição da capa ideal (50-80 palavras) incluindo:
- Elemento visual principal
- Posição e estilo do título
- Cores e atmosfera
- Elementos de apoio

---

### INSTRUÇÃO FINAL ###
Utilize a imagem anexada como canvas base. Crie uma capa de Reel profissional no formato 1080 x 1920 px (9:16), pronta para publicação no Instagram.
"""
        return prompt.strip()

    def _build_story_image_prompt(self, post_data: Dict, content: str) -> str:
        """Build prompt specifically for story images using structured format."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        further_details = post_data.get('further_details', '')

        creator_profile_data = self.get_creator_profile_data()
        visual_style = creator_profile_data.get('visual_style', {})
        visual_style_name = visual_style.get('name', '') if isinstance(visual_style, dict) else ''
        visual_style_description = visual_style.get('description', '') if isinstance(visual_style, dict) else ''
        color_palette = self._format_color_palette(creator_profile_data.get('color_palette', []))

        prompt = f"""
### PERSONA ###
Você é um designer de Stories premiado, especialista em criar artes que geram alto engajamento no Instagram. Trabalhou com marcas como FutureBrand e Pentagram, dominando o equilíbrio entre estética premium e comunicação efetiva em formato vertical.

---

### CONTEXTO ###
Você está criando um Story para "{creator_profile_data.get('business_name', 'Não informado')}".

**Dados do Negócio:**
- Nicho/Setor: {creator_profile_data.get('specialization', 'Não informado')}
- Descrição: {creator_profile_data.get('business_description', 'Não informado')}
- Tom de voz: {creator_profile_data.get('voice_tone', 'Profissional')}

**Público-Alvo:**
- Perfil: {creator_profile_data.get('target_audience', 'Não informado')}
- Interesses: {creator_profile_data.get('target_interests', 'Não informado')}

**Identidade Visual:**
- Paleta de cores: {color_palette}

**Dados do Story:**
- Assunto: {name}
- Objetivo: {objective}
- Detalhes: {further_details if further_details else 'Nenhum'}

---

### TAREFA ###
Crie uma arte de Story que:
1. Capture atenção instantânea (usuários gastam ~1.7s por Story)
2. Comunique a mensagem de forma clara e impactante
3. Gere engajamento (resposta, compartilhamento, clique)
4. Mantenha a identidade visual da marca

---

### ESTILO VISUAL OBRIGATÓRIO: {visual_style_name if visual_style_name else 'Premium Moderno'} ###
{visual_style_description if visual_style_description else 'Design premium e moderno. Estética minimalista com uso inteligente de espaço negativo. Hierarquia visual clara com título em destaque. Acabamento de agência de alto nível.'}

---

### DIRETRIZES TÉCNICAS ###
- **Formato:** 1080 x 1920 px (proporção 9:16 vertical)
- **Título:** Máximo 5 palavras, bold, alto impacto
- **Safe Zone:** 10% de margem nas bordas (evitar cortes)
- **Cores:** OBRIGATÓRIO usar paleta da marca: {color_palette}
- **Tipografia:** Inter, Montserrat, Poppins ou similar (suporte PT-BR)
- **Qualidade:** Premium, nível de agência

---

### HIERARQUIA VISUAL ###
1. **Título principal** - Elemento âncora, maior destaque
2. **Espaço negativo** - Respiro visual, menos é mais
3. **Elementos de apoio** - Sutis, reforçam o tema

---

{_build_logo_prompt_section(
    business_name=creator_profile_data.get('business_name', 'Marca'),
    color_palette=creator_profile_data.get('color_palette', [])
)}

---

### RESTRIÇÕES (O QUE EVITAR) ###
- Evitar poluição visual ou excesso de elementos
- Evitar textos longos ou parágrafos
- Evitar cores fora da paleta da marca
- Evitar imagens genéricas de banco
- Evitar criar logomarca fictícia
- Evitar fontes que não suportem acentos PT-BR
- Evitar elementos muito próximos às bordas

---

### REGRAS DE TEXTO PT-BR ###
- Todo texto OBRIGATORIAMENTE em Português do Brasil
- Ortografia 100% correta (verificar acentos, crase, concordância)
- Palavras como "saúde", "você", "é" devem estar acentuadas
- Validar cada palavra antes de renderizar

---

### FORMATO DE SAÍDA ###
Gere uma descrição da arte ideal (60-80 palavras) incluindo:
- Composição e layout
- Título sugerido (máx 5 palavras)
- Cores predominantes (da paleta)
- Elementos visuais de apoio
- Atmosfera/mood

---

### INSTRUÇÃO FINAL ###
Utilize a imagem anexada como canvas base. Crie uma arte de Story premium no formato 1080 x 1920 px (9:16), com texto em PT-BR perfeito, pronta para publicação no Instagram.
"""
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

    def build_historical_analysis_prompt(self, post_data: Dict) -> str:
        """Build the prompt for historical analysis and new direction creation."""
        name = post_data.get('name', '')
        objective = post_data.get('objective', '')
        further_details = post_data.get('further_details', '')
        creator_profile_data = self.get_creator_profile_data()

        prompt = f"""
Você é um estrategista criativo especializado em copywriting e conteúdo digital, responsável por garantir que cada nova campanha gerada mantenha qualidade, coerência e originalidade absoluta.
Sua função é analisar o histórico de conteúdos anteriores, entender o estilo, linguagem e temas já abordados, e criar um novo direcionamento criativo inédito, mantendo todas as regras, estrutura e padrão definidos no Prompt Mestre.
O resultado deve ser obrigatoriamente retornado no formato JSON descrito no final deste prompt.


🧾 DADOS DE PERSONALIZAÇÃO DO CLIENTE:

Nome do negócio: {creator_profile_data.get('business_name', '')}

Telefone do negócio: {creator_profile_data.get('business_phone', '')}

Setor/Nicho: {creator_profile_data.get('specialization', '')}

Descrição do negócio: {creator_profile_data.get('business_description', '')}

Público-alvo: {creator_profile_data.get('target_audience', '')}

Interesses do público-alvo: {creator_profile_data.get('target_interests', '')}

Localização do negócio: {creator_profile_data.get('business_location', '')}

Paleta de cores: {creator_profile_data.get('color_palette', '')}

Tom de voz: {creator_profile_data.get('voice_tone', '')}

🎯 OBJETIVO GERAL:

Assunto: {name}

Objetivo: {objective}

Mais detalhes: {further_details}

Temas sempre atualizados e relevantes para o público.

🪶 REGRAS PARA A COPY DO FEED:

Estrutura AIDA (Atenção, Interesse, Desejo, Ação):

Comece com uma frase ou pergunta envolvente e natural.

Desenvolva a mensagem com fluidez, contexto e empatia.

Gere identificação e desperte emoção.

Finalize com uma única CTA coerente e natural.

Estilo e tom:

Texto fluido, natural e pronto para publicação.

Parágrafos curtos e bem espaçados.

Média de 5 emojis por texto, usados de forma natural e coerente.

Linguagem ajustada ao tom de voz ({creator_profile_data.get('voice_tone', '')}) e público-alvo ({creator_profile_data.get('target_audience', '')}).

Use referências, expressões e temas em alta nas trends do nicho.

Evite sensacionalismo e exageros.

Personalização:

Adapte a linguagem e exemplos conforme o nicho e localização do cliente ({creator_profile_data.get('specialization', '')}, {creator_profile_data.get('business_location', '')}).

Faça alusões sutis ao negócio ({creator_profile_data.get('business_name', '')}) quando couber.

📦 FORMATO DE SAÍDA:

Gere a resposta exatamente neste formato:

🧩 1. Conteúdo de Feed (Copy Principal):

[Texto completo da copy, com média de 5 emojis bem distribuídos, pronto para publicação no Feed.]

Como sugestão para escrever na imagem:

Título: [Frase curta e chamativa — até 8 palavras — diferente das anteriores , sem usar as palavras 'Conteúdo Diário' ou 'Dica do Dia' ou relacionados] 

Subtítulo: [Frase complementar breve e criativa — formato sempre variado]

CTA: [Chamada natural e coerente com o conteúdo — alternada diariamente]

Descrição para gerar a imagem (sem texto):
Gere uma descrição detalhada de uma imagem profissional no tamanho 1080 x 1350 px (proporção 4:5), formato vertical otimizado para o Feed.

A imagem deve ser:


🪶 DIRETRIZES DE ESTILO:
Mantenha todas as regras, estrutura e padrões de qualidade do Prompt Mestre.

Preserve o tom de voz da marca ({creator_profile_data.get('voice_tone', '')}) e o perfil do público.

Busque inovação criativa dentro do mesmo contexto — sem descaracterizar o estilo.

Se inspire em novas tendências atuais do nicho ({creator_profile_data.get('specialization', '')}) e expressões recentes nas redes.

A ideia deve parecer nova e empolgante, sem soar genérica ou repetitiva.

⚙️ FORMATO DE SAÍDA (OBRIGATÓRIO):
A resposta deve ser entregue estritamente em formato JSON, seguindo exatamente esta estrutura:
{{
  "historical_analysis": "",
  "avoid_list": [],
  "new_direction": "",
  "new_headline": "",
  "new_subtitle": "",
  "new_cta": ""
}}

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

    def build_automatic_post_prompt(self, analysis_data: Dict = None) -> str:
        """Build prompt for automatic post creation based on creator profile."""
        creator_profile_data = self.get_creator_profile_data()

        try:
            prompt = f"""
Você é um especialista em copywriting estratégico, criativo e persuasivo, com foco em conteúdos para redes sociais (Instagram, Facebook, LinkedIn, etc.).
Sua missão é gerar campanhas completas e personalizadas, com base nas informações do onboarding do cliente e obrigatoriamente no JSON gerado pelo módulo “Entendimento Histórico”.
⚠️ Atenção:
 Este prompt só deve funcionar se o JSON abaixo for recebido corretamente.
 Caso algum campo esteja vazio ou ausente, o conteúdo não deve ser gerado.
Esse JSON define o direcionamento criativo e é essencial para garantir que o conteúdo diário seja inédito, original e não repetitivo.

🧠 ENTRADA OBRIGATÓRIA – JSON DO ENTENDIMENTO HISTÓRICO
Você deve receber obrigatoriamente o seguinte bloco JSON:
{{
  "historical_analysis": "",
  "avoid_list": [],
  "new_direction": "",
  "new_headline": "",
  "new_subtitle": "",
  "new_cta": ""
}}

Função de cada campo:
- historical_analysis: resumo do que foi feito anteriormente (usado apenas para referência, sem repetir nada).
- avoid_list: lista de ideias, expressões, CTAs ou palavras que devem ser evitadas integralmente.
- new_direction: principal linha criativa e conceito que devem guiar toda a nova campanha.
- new_headline / new_subtitle / new_cta: ideias e variações criativas que devem inspirar os novos textos e chamadas.

🧠 JSON RECEBIDO:

{analysis_data}

🧾 DADOS DE PERSONALIZAÇÃO DO CLIENTE (do onboarding):

Nome do negócio: {creator_profile_data.get('business_name', '')}

Telefone do negócio: {creator_profile_data.get('business_phone', '')}

Setor/Nicho: {creator_profile_data.get('specialization', '')}

Descrição do negócio: {creator_profile_data.get('business_description', '')}

Público-alvo: {creator_profile_data.get('target_audience', '')}

Interesses do público-alvo: {creator_profile_data.get('target_interests', '')}

Localização do negócio: {creator_profile_data.get('business_location', '')}

Paleta de cores: {creator_profile_data.get('color_palette', '')}

Tom de voz: {creator_profile_data.get('voice_tone', '')}

🎯 OBJETIVO GERAL

Gerar uma campanha diária completa com base:
- no novo direcionamento criativo (new_direction) do JSON;
- nos dados do onboarding do cliente;
- e nas trends atuais do nicho ({creator_profile_data.get('specialization', '')}).

Todos os conteúdos devem ser:
- Totalmente novos e originais;
- Coerentes com o histórico e identidade da marca;
- Aderentes ao público e ao tom de voz ({creator_profile_data.get('voice_tone', '')});
- E sem repetir nada do que aparece em avoid_list.

🪶 REGRAS PARA O CONTEÚDO DE FEED
Base Criativa:
- Toda a copy deve ser construída a partir do conteúdo de new_direction.
- Use new_headline, new_subtitle e new_cta como inspiração direta, mas reescrevendo-os de forma fluida e contextual.
- Estrutura AIDA (Atenção, Interesse, Desejo, Ação):
- Abertura envolvente e atual;
- Desenvolvimento empático e leve;
- Valor e conexão emocional;
- Fechamento com uma única CTA natural, coerente com o contexto do dia.

Estilo e tom:
- Texto fluido e natural, pronto para o Feed;
- Média de 5 emojis, aplicados com naturalidade;
- Parágrafos curtos e escaneáveis;
- Linguagem adaptada ao público ({creator_profile_data.get('target_audience', '')});
- Sempre alinhado ao tom de voz ({creator_profile_data.get('voice_tone', '')});
- Títulos, subtítulos e CTAs devem variar diariamente, seguindo o JSON atual.

📦 FORMATO DE SAÍDA
🧩 1. Conteúdo de Feed (Copy Principal):
[Texto completo e pronto para o Feed — fluido, original e com média de 5 emojis.]

Como sugestão para escrever na imagem:
- Título: inspirado em new_headline — curto (até 8 palavras), criativo e diferente de dias anteriores.
- Subtítulo: inspirado em new_subtitle — complementar, empático e inédito.
- CTA: inspirada em new_cta — natural, coerente e sem repetições.

Descrição para gerar a imagem (sem texto):
- Crie uma imagem moderna e realista que traduza visualmente o tema do post, mostrando cenas, ambientes ou ações autênticas que representem o assunto.
- Exemplo:
  - Se o tema for autocuidado, mostre uma mulher sorrindo em um ambiente relaxante;
  - Se for marketing, mostre conexão, criatividade ou energia coletiva.
- ⚠️ Evite qualquer imagem de pessoas em frente a computadores, notebooks ou celulares, a menos que o tema peça explicitamente isso.
- A imagem deve seguir estas diretrizes: Tamanho 1080 x 1350 px (4:5 vertical);
- Sem texto, número, fonte, logotipo, borda, moldura ou watermark;
- Realista e de alta qualidade, com aparência de design premiado;
- Coerente com a paleta de cores ({creator_profile_data.get('color_palette', '')});
- Representando o público ({creator_profile_data.get('target_audience', '')}) e localização do negócio ({creator_profile_data.get('business_location', '')});
- Inspirada em tendências visuais do momento;
- Estilo profissional, harmônico e natural, como se fosse criada por um designer de alto nível.

📱 2. Ideias de Stories (5 sugestões):
Crie 5 ideias de Stories derivadas do mesmo new_direction.
Devem:
- Ser coerentes com o tema do dia;
- Estimular engajamento;
- Variar formatos (enquete, pergunta, bastidor, dica, reflexão);
- Estar alinhadas ao tom de voz ({creator_profile_data.get('voice_tone', '')}) e interesses do público.

Exemplo:
 1️⃣ [Ideia 1 — contextualizada com o new_direction]
 2️⃣ [Ideia 2 — baseada em tendência atual]
 3️⃣ [Ideia 3 — interação leve e natural]
 4️⃣ [Ideia 4 — dica ou insight rápido]
 5️⃣ [Ideia 5 — encerramento inspirador do dia]

🎬 3. Ideia de Roteiro para Reels:
Crie 1 roteiro curto (20–40 segundos) diretamente conectado ao new_direction.
Estrutura:
- Abertura (3s): gancho forte, inspirado nas trends atuais;
- Desenvolvimento: história, dica ou insight relevante;
- Fechamento: CTA leve, coerente e original.

O roteiro deve:
- Ser dinâmico e natural;
- Refletir o tom de voz ({creator_profile_data.get('voice_tone', '')});
- Evitar todos os termos da avoid_list;
- Trazer ideias visuais atuais e criativas (gestos, cenas, falas, transições).

📅 CONTEXTO DE USO
Este prompt não deve funcionar sem o JSON do Entendimento Histórico.
Ao gerar o conteúdo:
- Use new_direction como guia criativo principal;
- Evite todos os elementos em avoid_list;
- Inspire-se em new_headline, new_subtitle, e new_cta;
- Aplique todas as regras do Prompt Mestre (estrutura AIDA, tom, qualidade visual, proibições de texto na imagem, etc.);
- E produza uma campanha diária original, profissional e alinhada às trends do momento.

⚙️ FORMATO DE SAÍDA (OBRIGATÓRIO):
A resposta deve ser entregue estritamente em formato JSON, seguindo exatamente esta estrutura:
{{
  "feed_html": "",
  "feed_image_description": "",
  "story_html": "",
  "reels_html": "",
}}

Apenas os campos "feed_html", "story_html" e "reels_html" devem vir formatados como HTML, deixando sempre tópicos e títulos em negrito para melhorar a UI, OBRIGATORIAMENTE.
        """

            return prompt.strip()

        except Exception:
            import traceback
            traceback.print_exc()
            raise
