"""
Testes para o botao 'Criar este Conteudo' no email de oportunidades.
"""
import os
import urllib.parse
from unittest.mock import patch

from django.test import TestCase


class TestCreateContentButtonInEmail(TestCase):
    """Testa o botao de criar conteudo no template de email."""

    def test_opportunity_item_includes_create_button(self):
        """Item de oportunidade deve incluir botao de criar."""
        from ClientContext.utils.opportunities_email import _generate_opportunity_item

        item = {
            "titulo_ideia": "IA substituindo empregos",
            "descricao": "Discussao sobre o futuro do trabalho",
            "score": 95,
            "url_fonte": "https://example.com",
            "enriched_sources": [],
            "enriched_analysis": "Analise do tema"
        }
        colors = {
            "bg": "#fef2f2",
            "border": "#ef4444",
            "text": "#dc2626",
            "emoji": "🔥"
        }

        result = _generate_opportunity_item(item, colors, 0, "polemica")

        self.assertIn("Criar este Conteúdo", result)
        self.assertIn("/create?", result)

    def test_create_button_has_correct_url_params(self):
        """Botao deve ter parametros de URL corretos."""
        from ClientContext.utils.opportunities_email import _generate_opportunity_item

        item = {
            "titulo_ideia": "Teste de Titulo",
            "descricao": "Descricao",
            "score": 80,
            "url_fonte": "",
            "enriched_sources": [],
            "enriched_analysis": ""
        }
        colors = {"bg": "#f0fdf4", "border": "#22c55e", "text": "#16a34a", "emoji": "🧠"}

        result = _generate_opportunity_item(item, colors, 0, "educativo")

        # Verifica parametros na URL
        self.assertIn("topic=", result)
        self.assertIn("category=educativo", result)
        self.assertIn("score=80", result)

    def test_create_button_url_encodes_topic(self):
        """Titulo deve ser URL encoded."""
        from ClientContext.utils.opportunities_email import _generate_opportunity_item

        item = {
            "titulo_ideia": "Tema com espacos e acentos",
            "descricao": "Descricao",
            "score": 70,
            "url_fonte": "",
            "enriched_sources": [],
            "enriched_analysis": ""
        }
        colors = {"bg": "#f0fdf4", "border": "#22c55e", "text": "#16a34a", "emoji": "🧠"}

        result = _generate_opportunity_item(item, colors, 0, "educativo")

        # Verifica que espacos sao codificados
        self.assertIn("topic=Tema%20com%20espa", result)

    @patch.dict(os.environ, {"FRONTEND_URL": "https://app.test.com"})
    def test_create_button_uses_frontend_url_env(self):
        """Botao deve usar FRONTEND_URL do ambiente."""
        from ClientContext.utils.opportunities_email import _generate_opportunity_item

        item = {
            "titulo_ideia": "Teste",
            "descricao": "Descricao",
            "score": 50,
            "url_fonte": "",
            "enriched_sources": [],
            "enriched_analysis": ""
        }
        colors = {"bg": "#f0fdf4", "border": "#22c55e", "text": "#16a34a", "emoji": "🧠"}

        result = _generate_opportunity_item(item, colors, 0, "educativo")

        self.assertIn("https://app.test.com/create", result)

    def test_create_button_has_correct_styling(self):
        """Botao deve ter estilo correto."""
        from ClientContext.utils.opportunities_email import _generate_opportunity_item

        item = {
            "titulo_ideia": "Teste",
            "descricao": "Descricao",
            "score": 50,
            "url_fonte": "",
            "enriched_sources": [],
            "enriched_analysis": ""
        }
        colors = {"bg": "#f0fdf4", "border": "#22c55e", "text": "#16a34a", "emoji": "🧠"}

        result = _generate_opportunity_item(item, colors, 0, "educativo")

        # Verifica estilos do botao
        self.assertIn("display: inline-block", result)
        self.assertIn("border-radius: 6px", result)
        self.assertIn("text-decoration: none", result)

    def test_create_button_uses_category_color(self):
        """Botao deve usar cor da categoria."""
        from ClientContext.utils.opportunities_email import _generate_opportunity_item

        item = {
            "titulo_ideia": "Teste",
            "descricao": "Descricao",
            "score": 50,
            "url_fonte": "",
            "enriched_sources": [],
            "enriched_analysis": ""
        }
        # Cor vermelha da categoria polemica
        colors = {"bg": "#fef2f2", "border": "#ef4444", "text": "#dc2626", "emoji": "🔥"}

        result = _generate_opportunity_item(item, colors, 0, "polemica")

        # Verifica que usa a cor da categoria
        self.assertIn("#ef4444", result)

    def test_create_button_handles_empty_title(self):
        """Botao deve lidar com titulo vazio."""
        from ClientContext.utils.opportunities_email import _generate_opportunity_item

        item = {
            "titulo_ideia": "",
            "descricao": "Descricao",
            "score": 50,
            "url_fonte": "",
            "enriched_sources": [],
            "enriched_analysis": ""
        }
        colors = {"bg": "#f0fdf4", "border": "#22c55e", "text": "#16a34a", "emoji": "🧠"}

        result = _generate_opportunity_item(item, colors, 0, "educativo")

        # Deve gerar URL mesmo com titulo vazio
        self.assertIn("/create?topic=", result)

    def test_create_button_handles_special_characters(self):
        """Botao deve lidar com caracteres especiais."""
        from ClientContext.utils.opportunities_email import _generate_opportunity_item

        item = {
            "titulo_ideia": "Tema & teste <script>",
            "descricao": "Descricao",
            "score": 50,
            "url_fonte": "",
            "enriched_sources": [],
            "enriched_analysis": ""
        }
        colors = {"bg": "#f0fdf4", "border": "#22c55e", "text": "#16a34a", "emoji": "🧠"}

        result = _generate_opportunity_item(item, colors, 0, "educativo")

        # Caracteres especiais devem ser codificados na URL
        self.assertIn("topic=", result)
        # & deve ser codificado como %26
        self.assertIn("%26", result)


class TestGenerateOpportunitiesHtml(TestCase):
    """Testa a geracao do HTML completo de oportunidades."""

    def test_opportunities_html_includes_create_buttons(self):
        """HTML de oportunidades deve incluir botoes de criar."""
        from ClientContext.utils.opportunities_email import _generate_opportunities_html

        # Formato correto: categoria -> {titulo, items}
        opportunities_data = {
            "polemica": {
                "titulo": "Temas Polemicos",
                "items": [
                    {
                        "titulo_ideia": "Tema 1",
                        "descricao": "Desc 1",
                        "score": 90,
                        "url_fonte": "",
                        "enriched_sources": [],
                        "enriched_analysis": ""
                    }
                ]
            },
            "educativo": {
                "titulo": "Temas Educativos",
                "items": [
                    {
                        "titulo_ideia": "Tema 2",
                        "descricao": "Desc 2",
                        "score": 85,
                        "url_fonte": "",
                        "enriched_sources": [],
                        "enriched_analysis": ""
                    }
                ]
            }
        }

        result = _generate_opportunities_html(opportunities_data)

        # Deve ter 2 botoes (um por oportunidade)
        count = result.count("Criar este Conteúdo")
        self.assertEqual(count, 2)

    def test_opportunities_html_has_different_categories(self):
        """HTML deve ter categorias diferentes nos botoes."""
        from ClientContext.utils.opportunities_email import _generate_opportunities_html

        opportunities_data = {
            "polemica": {
                "titulo": "Temas Polemicos",
                "items": [
                    {
                        "titulo_ideia": "Tema Polemico",
                        "descricao": "Desc",
                        "score": 90,
                        "url_fonte": "",
                        "enriched_sources": [],
                        "enriched_analysis": ""
                    }
                ]
            },
            "educativo": {
                "titulo": "Temas Educativos",
                "items": [
                    {
                        "titulo_ideia": "Tema Educativo",
                        "descricao": "Desc",
                        "score": 85,
                        "url_fonte": "",
                        "enriched_sources": [],
                        "enriched_analysis": ""
                    }
                ]
            }
        }

        result = _generate_opportunities_html(opportunities_data)

        self.assertIn("category=polemica", result)
        self.assertIn("category=educativo", result)
