#!/usr/bin/env python
"""
Script para gerar imagens de preview dos 18 estilos visuais.
Usa o fluxo correto da main com Gemini Native Image Generation.

Uso:
    cd PostNow-REST-API
    source venv/bin/activate
    python scripts/generate_style_previews.py

    # Gerar apenas um estilo específico:
    python scripts/generate_style_previews.py --style-id=1

    # Modo dry-run (não salva):
    python scripts/generate_style_previews.py --dry-run
"""

import os
import sys
import time
import uuid
import base64
import argparse
import logging
from pathlib import Path
from datetime import datetime
from time import sleep

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sonora_REST_API.settings')
os.environ['USE_SQLITE'] = 'True'

import django
django.setup()

from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env')

import boto3
from botocore.exceptions import ClientError

# Google Gemini - usando a mesma API da main
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("AVISO: google-genai não instalado. Execute: pip install google-genai")

from CreatorProfile.models import VisualStylePreference

logger = logging.getLogger(__name__)


# Dados fixos do onboarding PostNow (conforme especificado no plano)
POSTNOW_DATA = {
    'business_name': 'Postnow',
    'business_website': 'https://www.postnow.com.br/',
    'business_instagram_handle': '@postnow_',
    'specialization': 'Ferramenta de Criatividade',
    'business_description': 'Profissionais liberais ganham autoridade e atraem clientes sem perder tempo com marketing complicado. Com a Postnow, em minutos eles têm roteiros, posts e ideias prontas enviadas todos os dias no email',
    'business_purpose': 'Criar constância de postagem para profissionais liberais, pequenas e médias empresas',
    'brand_personality': 'Criativa, forte e com autoridade',
    'target_audience': 'Profissionais liberais',
    'target_interests': 'Marketing digital, produtividade, crescimento profissional',
    'voice_tone': 'Autoridade',
    'business_location': 'Brasil',
    'color_palette': ['#8B5CF6', '#FFFFFF', '#4B4646', '#A855F7', '#EC4899'],
}

# Logo da PostNow em base64 (carregada do arquivo)
POSTNOW_LOGO_PATH = Path(__file__).parent / 'postnow_logo.png'


def load_postnow_logo_base64() -> str:
    """Carrega a logo da PostNow e retorna em base64."""
    if not POSTNOW_LOGO_PATH.exists():
        logger.warning(f"Logo não encontrada em {POSTNOW_LOGO_PATH}")
        return None

    with open(POSTNOW_LOGO_PATH, 'rb') as f:
        logo_bytes = f.read()

    return base64.b64encode(logo_bytes).decode('utf-8')


class S3ImageUploader:
    """Serviço para upload de imagens no S3 (mesmo padrão da main)."""

    def __init__(self):
        self.bucket_name = os.getenv('AWS_S3_IMAGE_BUCKET', 'postnow-image-bucket-prod')
        self.region = os.getenv('AWS_S3_REGION_NAME', 'sa-east-1')

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=self.region
        )

    def upload_image(self, image_bytes: bytes, style_name: str) -> str:
        """Upload imagem para S3 e retorna URL pública."""
        # Gerar nome único (padrão da main)
        unique_id = str(uuid.uuid4())
        safe_name = style_name.lower().replace(' ', '-').replace('ã', 'a').replace('á', 'a').replace('é', 'e').replace('ê', 'e').replace('í', 'i').replace('ô', 'o').replace('ú', 'u')
        filename = f"style-previews/{safe_name}_{unique_id[:8]}.png"

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=image_bytes,
                ContentType='image/png',
            )

            # Gerar URL pública
            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{filename}"
            logger.info(f"Image uploaded to S3: {url}")
            return url

        except ClientError as e:
            raise Exception(f"Erro ao fazer upload para S3: {e}")


class GeminiImageGenerator:
    """
    Gerador de imagens usando Gemini Native Image Generation.
    Usa o mesmo fluxo da main: generate_content_stream com response_modalities=["IMAGE"]
    """

    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada no .env")

        # Configurar cliente Gemini (mesmo padrão da main)
        self.client = genai.Client(api_key=api_key)

        # Modelos de imagem (da main: services/ai_service.py)
        self.image_models = [
            'gemini-3-pro-image-preview',
            'gemini-2.5-flash-preview-05-20',
            'gemini-2.0-flash-exp-image-generation',
        ]

        # Configuração de geração de imagem (da main: services/ai_service.py)
        # Inclui temperature e top_p conforme a main
        self.generate_image_config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.9,
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="4:5",  # Formato correto do Instagram Feed
            ),
        )

        self.max_retries = 3

    def generate_image(self, prompt: str, image_attachment: str = None) -> bytes:
        """
        Gera imagem usando Gemini Native Image Generation.
        Segue o fluxo da main: _try_model_with_retries -> _try_generate_image
        """
        last_error = None

        for model in self.image_models:
            for attempt in range(self.max_retries):
                try:
                    result = self._try_generate_image(model, prompt, image_attachment)
                    if result:
                        print(f"    ✅ Modelo {model} funcionou na tentativa {attempt + 1}")
                        return result
                    else:
                        raise Exception("Nenhuma imagem recebida do modelo")

                except Exception as e:
                    error_str = str(e)
                    last_error = e
                    print(f"    ⚠️  Erro com {model} (tentativa {attempt + 1}): {error_str[:100]}")

                    if not self._is_retryable_error(error_str):
                        print(f"    ⏭️  Erro não-retryable, tentando próximo modelo...")
                        break  # Tenta próximo modelo

                    if attempt < self.max_retries - 1:
                        delay = 5 * (2 ** attempt)
                        print(f"    ⏳ Aguardando {delay}s antes de retry...")
                        sleep(delay)

        raise Exception(f"Todos os modelos falharam. Último erro: {last_error}")

    def _try_generate_image(self, model: str, prompt: str, image_attachment: str = None) -> bytes:
        """
        Tenta gerar imagem com um modelo específico.
        Segue exatamente o padrão da main: services/ai_service.py:_try_generate_image
        """
        image_bytes = None
        print(f"    Tentando modelo: {model}")

        # Construir conteúdo (mesmo padrão da main)
        contents = types.Content(
            role='user',
            parts=[]
        )

        # Adicionar imagem de attachment se fornecida (logo)
        if image_attachment:
            contents.parts.append(types.Part.from_bytes(
                mime_type="image/png",
                data=base64.b64decode(image_attachment),
            ))

        # Adicionar prompt de texto
        contents.parts.append(types.Part.from_text(text=prompt))

        # Gerar usando stream (mesmo padrão da main)
        for chunk in self.client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=self.generate_image_config
        ):
            if not self._check_for_content_parts(chunk):
                continue

            part = chunk.candidates[0].content.parts[0]

            if hasattr(part, 'inline_data') and part.inline_data and hasattr(part.inline_data, 'data') and part.inline_data.data:
                image_bytes = part.inline_data.data
                break
            elif hasattr(part, 'text') and part.text:
                continue

        if not image_bytes:
            raise Exception("No image data received from the model")

        return image_bytes

    def _check_for_content_parts(self, chunk) -> bool:
        """Verifica se o chunk tem partes de conteúdo válidas (da main)."""
        if not hasattr(chunk, 'candidates') or chunk.candidates is None:
            return False
        if (
                len(chunk.candidates) == 0
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
                or len(chunk.candidates[0].content.parts) == 0
        ):
            return False
        return True

    def _is_retryable_error(self, error_str: str) -> bool:
        """Determina se o erro é retryable (da main)."""
        retryable_indicators = [
            '503', '500', 'internal', 'unavailable', 'overloaded',
            'timeout', 'temporarily', '429', 'No image data received'
        ]
        return any(indicator in error_str.lower() for indicator in retryable_indicators)


def build_style_preview_prompt(style: VisualStylePreference) -> str:
    """
    Constrói prompt para preview de um estilo específico.
    Segue a estrutura do prompt_service.py:_build_feed_image_prompt

    IMPORTANTE: Todas as imagens usam o MESMO TEMA para facilitar
    a comparação entre estilos pelo usuário no onboarding.
    """
    color_palette = ', '.join(POSTNOW_DATA['color_palette'])

    # Tema ÚNICO para todas as imagens de preview
    # Isso permite que o usuário compare apenas o ESTILO VISUAL
    TEMA_PRINCIPAL = "CONQUISTE MAIS CLIENTES"
    SUBTEMA = "Com conteúdo que gera autoridade"

    prompt = f"""
### PERSONA ###
Você é um diretor de arte premiado internacionalmente, com 15 anos de experiência criando campanhas visuais para marcas como Apple, Nike e Airbnb. Especialista em design para redes sociais, você domina composição, teoria das cores e tendências visuais contemporâneas.

---

### CONTEXTO ###
Você está criando uma imagem de PREVIEW/DEMONSTRAÇÃO do estilo visual "{style.name}" para o Instagram de "{POSTNOW_DATA['business_name']}".

Esta imagem será exibida no onboarding para que usuários escolham seus estilos visuais preferidos. O usuário verá várias imagens lado a lado, cada uma em um estilo diferente, mas TODAS com o mesmo tema/conteúdo para facilitar a comparação.

**Dados do Negócio:**
- Nicho/Setor: {POSTNOW_DATA['specialization']}
- Descrição: {POSTNOW_DATA['business_description']}
- Tom de voz da marca: {POSTNOW_DATA['voice_tone']}

**Público-Alvo:**
- Perfil: {POSTNOW_DATA['target_audience']}
- Interesses: {POSTNOW_DATA['target_interests']}

**Identidade Visual da Marca:**
- Paleta de cores: {color_palette}

---

### CONTEÚDO OBRIGATÓRIO DA IMAGEM ###
A imagem DEVE conter os seguintes textos renderizados:

1. **Título Principal (DESTAQUE):** "{TEMA_PRINCIPAL}"
   - Este é o texto mais importante da imagem
   - Deve estar em posição de destaque
   - Tipografia impactante conforme o estilo

2. **Subtítulo (opcional):** "{SUBTEMA}"
   - Complementa o título principal
   - Menor que o título, mas legível

3. **Logo/Marca:** Use a LOGO ANEXADA (imagem PostNow)
   - A logo foi anexada a esta requisição - USE-A na composição
   - Posição discreta mas visível (canto inferior ou superior)
   - Integre a logo anexada elegantemente ao design
   - NÃO escreva "POSTNOW" como texto - use a logo gráfica anexada

---

### TAREFA ###
Crie uma imagem que demonstre perfeitamente o estilo visual "{style.name}" aplicado ao tema "{TEMA_PRINCIPAL}".

A imagem deve:
1. Demonstrar CLARAMENTE as características visuais do estilo "{style.name}"
2. Renderizar o texto "{TEMA_PRINCIPAL}" de forma impactante e legível
3. Parecer um post real de Instagram pronto para publicação
4. Usar obrigatoriamente a paleta de cores: {color_palette}
5. Ter qualidade profissional de agência de alto nível

---

### ESTILO VISUAL OBRIGATÓRIO: {style.name} ###
{style.description}

---

### DIRETRIZES TÉCNICAS ###
- **Formato:** 1080 x 1350 px (proporção 4:5 vertical para Feed)
- **Qualidade:** Ultra-detalhada, renderização profissional 4K
- **Iluminação:** Conforme especificado no estilo visual acima
- **Composição:** Conforme especificado no estilo visual acima
- **Cores:** Usar OBRIGATORIAMENTE a paleta da marca: {color_palette}
- **Tipografia:** Conforme especificado no estilo visual, mas garantir legibilidade

---

### REGRAS DE RENDERIZAÇÃO DE TEXTO E LOGO ###
- O texto "{TEMA_PRINCIPAL}" DEVE estar claramente legível na imagem
- USE A LOGO GRÁFICA ANEXADA (não escreva "POSTNOW" como texto)
- A logo anexada deve ser integrada na composição visual
- Textos devem ser escritos em português do Brasil
- NÃO renderize hashtags na imagem
- NÃO renderize códigos HEX das cores na imagem
- NÃO renderize o termo "(PT-BR)" na imagem
- NÃO substitua a logo por texto - use a imagem da logo anexada

---

### RESTRIÇÕES (O QUE EVITAR) ###
- NÃO incluir rostos humanos realistas
- NÃO incluir logos de outras marcas
- NÃO incluir marcas d'água
- NÃO incluir textos além dos especificados acima
- NÃO incluir elementos de interface ou frames de celular
- NÃO usar cores fora da paleta da marca
- NÃO criar imagens genéricas de banco de imagens
- NÃO escrever o texto com erros ortográficos

---

### INSTRUÇÃO FINAL ###
Crie uma arte profissional que seja uma demonstração perfeita do estilo "{style.name}".

IMPORTANTE: Uma imagem de LOGO foi anexada a esta requisição. Use essa logo na composição da imagem final.

O resultado deve mostrar claramente:
- O texto "{TEMA_PRINCIPAL}" renderizado no estilo tipográfico característico
- A paleta de cores {color_palette} aplicada conforme o estilo
- A composição e elementos visuais típicos do estilo "{style.name}"
- A LOGO ANEXADA integrada elegantemente ao design (não escreva texto, use a imagem da logo)

A imagem deve fazer o usuário pensar: "Quero meus posts nesse estilo!"
"""
    return prompt.strip()


def generate_preview_for_style(
    style: VisualStylePreference,
    generator: GeminiImageGenerator,
    uploader: S3ImageUploader,
    logo_base64: str = None,
    dry_run: bool = False
) -> str:
    """Gera imagem de preview para um estilo específico."""

    # Construir prompt no padrão correto
    prompt = build_style_preview_prompt(style)

    if dry_run:
        print(f"  [DRY-RUN] Prompt gerado ({len(prompt)} chars)")
        print(f"  [DRY-RUN] Logo attachment: {'Sim' if logo_base64 else 'Não'}")
        return "https://example.com/dry-run-image.png"

    # Gerar imagem usando Gemini Native COM a logo como attachment
    print(f"  Gerando imagem com Gemini...")
    if logo_base64:
        print(f"  📎 Logo PostNow anexada como base para composição")
    image_bytes = generator.generate_image(prompt, image_attachment=logo_base64)

    # Upload para S3
    print(f"  Fazendo upload para S3...")
    image_url = uploader.upload_image(image_bytes, style.name)

    return image_url


def main():
    parser = argparse.ArgumentParser(
        description='Gera imagens de preview para os 18 estilos visuais (usando Gemini Native)'
    )
    parser.add_argument(
        '--style-id',
        type=int,
        help='ID de um estilo específico para gerar (opcional)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Modo teste - não gera nem salva imagens'
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Pula estilos que já têm preview_image_url'
    )
    parser.add_argument(
        '--regenerate',
        action='store_true',
        help='Regenera todas as imagens, mesmo as que já existem'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("🎨 GERADOR DE PREVIEWS - ESTILOS VISUAIS POSTNOW")
    print("   Usando Gemini Native Image Generation (fluxo correto)")
    print("=" * 70)
    print(f"Início: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Dry-run: {'Sim' if args.dry_run else 'Não'}")
    print(f"Modelo: gemini-3-pro-image-preview (fallback: gemini-2.5-flash)")
    print(f"Aspect Ratio: 4:5 (Instagram Feed)")
    print()

    # Verificar dependências
    if not GEMINI_AVAILABLE and not args.dry_run:
        print("❌ Biblioteca google-genai não disponível")
        print("   Execute: pip install google-genai")
        return

    # Carregar logo da PostNow
    logo_base64 = load_postnow_logo_base64()
    if logo_base64:
        print(f"✅ Logo PostNow carregada ({len(logo_base64)} chars base64)")
    else:
        print("⚠️  Logo PostNow não encontrada - imagens serão geradas sem logo")

    # Inicializar serviços
    generator = None
    uploader = None

    if not args.dry_run:
        try:
            print("  Inicializando Gemini Image Generator...")
            generator = GeminiImageGenerator()
            print("  ✅ Gemini Generator OK")
            print("  Inicializando S3 Uploader...")
            uploader = S3ImageUploader()
            print("  ✅ S3 Uploader OK")
            print("✅ Serviços inicializados")
        except Exception as e:
            import traceback
            print(f"❌ Erro ao inicializar serviços: {e}")
            traceback.print_exc()
            return

    # Buscar estilos
    if args.style_id:
        styles = VisualStylePreference.objects.filter(id=args.style_id)
        if not styles.exists():
            print(f"❌ Estilo com ID {args.style_id} não encontrado")
            return
    else:
        styles = VisualStylePreference.objects.all().order_by('id')

    total = styles.count()
    print(f"\n📊 Total de estilos: {total}")
    print()

    # Métricas
    success = 0
    failed = 0
    skipped = 0

    # Processar cada estilo
    for style in styles:
        print(f"[{style.id:2}/{total}] {style.name}")

        # Verificar se já tem preview (a menos que --regenerate)
        if not args.regenerate and args.skip_existing and style.preview_image_url:
            print(f"  ⏭️  Já tem preview: {style.preview_image_url[:50]}...")
            skipped += 1
            continue

        try:
            start_time = time.time()

            image_url = generate_preview_for_style(
                style=style,
                generator=generator,
                uploader=uploader,
                logo_base64=logo_base64,
                dry_run=args.dry_run
            )

            elapsed = time.time() - start_time

            # Salvar URL no banco
            if not args.dry_run:
                style.preview_image_url = image_url
                style.save()

            print(f"  ✅ Concluído em {elapsed:.1f}s")
            print(f"     URL: {image_url[:60]}...")
            success += 1

            # Pausa entre requisições para evitar rate limiting
            if not args.dry_run and style.id != styles.last().id:
                print(f"  ⏳ Aguardando 10s antes da próxima imagem...")
                time.sleep(10)

        except Exception as e:
            print(f"  ❌ Erro: {e}")
            failed += 1

        print()

    # Resumo
    print("=" * 70)
    print("📊 RESUMO")
    print("=" * 70)
    print(f"✅ Sucesso: {success}/{total}")
    print(f"❌ Falhas: {failed}/{total}")
    print(f"⏭️  Pulados: {skipped}/{total}")
    print()

    if not args.dry_run:
        estimated_cost = success * 0.23
        print(f"💰 Custo estimado: ${estimated_cost:.2f} USD")

    print(f"\n🏁 Concluído às {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 70)

    # Mostrar verificação
    if success > 0 and not args.dry_run:
        print("\n📝 Para verificar as URLs geradas:")
        print("   source venv/bin/activate && python -c \"")
        print("   import os; os.environ['DJANGO_SETTINGS_MODULE']='Sonora_REST_API.settings'")
        print("   os.environ['USE_SQLITE']='True'")
        print("   import django; django.setup()")
        print("   from CreatorProfile.models import VisualStylePreference")
        print("   for s in VisualStylePreference.objects.all():")
        print("       print(f'{s.id}. {s.name}: {s.preview_image_url}')\"")


if __name__ == '__main__':
    main()
