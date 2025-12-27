"""
Testes básicos para o app Campaigns.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal

from .models import Campaign, CampaignPost, CampaignDraft
from .services.campaign_builder_service import CampaignBuilderService
from .constants import calculate_campaign_cost


class CampaignModelTest(TestCase):
    """Testes do model Campaign."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_campaign(self):
        """Teste de criação básica de campanha."""
        campaign = Campaign.objects.create(
            user=self.user,
            name="Test Campaign",
            type='branding',
            objective="Test objective",
            structure='aida',
            duration_days=14,
            post_count=8
        )
        
        self.assertEqual(campaign.name, "Test Campaign")
        self.assertEqual(campaign.type, 'branding')
        self.assertEqual(campaign.status, 'draft')
    
    def test_campaign_str(self):
        """Teste de representação string."""
        campaign = Campaign.objects.create(
            user=self.user,
            name="AIDA Campaign",
            type='sales',
            objective="Test",
            structure='aida'
        )
        
        self.assertIn("AIDA Campaign", str(campaign))


class CampaignBuilderServiceTest(TestCase):
    """Testes do CampaignBuilderService."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testbuilder',
            email='builder@example.com',
            password='testpass123'
        )
        self.service = CampaignBuilderService()
    
    def test_calculate_cost(self):
        """Teste de cálculo de custo."""
        cost = calculate_campaign_cost(8, include_images=True)
        expected = (8 * 0.02) + (8 * 0.23)  # 8 textos + 8 imagens
        self.assertEqual(cost, expected)
    
    def test_calculate_cost_no_images(self):
        """Teste de custo sem imagens."""
        cost = calculate_campaign_cost(8, include_images=False)
        expected = 8 * 0.02  # Apenas textos
        self.assertEqual(cost, expected)


class CampaignDraftTest(TestCase):
    """Testes de CampaignDraft (auto-save)."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='draftuser',
            email='draft@example.com',
            password='testpass123'
        )
    
    def test_create_draft(self):
        """Teste de criação de draft."""
        draft = CampaignDraft.objects.create(
            user=self.user,
            current_phase='briefing',
            briefing_data={'objective': 'Test objective'}
        )
        
        self.assertEqual(draft.status, 'in_progress')
        self.assertEqual(draft.current_phase, 'briefing')
        self.assertIn('objective', draft.briefing_data)
    
    def test_draft_ordering(self):
        """Testa ordenação de drafts por updated_at."""
        draft1 = CampaignDraft.objects.create(
            user=self.user,
            current_phase='briefing'
        )
        draft2 = CampaignDraft.objects.create(
            user=self.user,
            current_phase='structure'
        )
        
        drafts = list(CampaignDraft.objects.all())
        # Deve vir mais recente primeiro
        self.assertEqual(drafts[0].id, draft2.id)
