import time
from abc import ABC, abstractmethod
from typing import Dict, List

from CreatorProfile.models import CreatorProfile
from django.contrib.auth.models import User


class ProgressTracker:
    """Track real progress of AI generation tasks."""

    def __init__(self):
        self.current_step = 0
        self.total_steps = 0
        self.step_details = []
        self.start_time = None

    def set_steps(self, steps: List[str]):
        """Set the steps for the generation process."""
        self.step_details = steps
        self.total_steps = len(steps)
        self.current_step = 0
        self.start_time = time.time()

    def next_step(self, step_name: str = None):
        """Move to next step."""
        if step_name:
            self.step_details[self.current_step] = step_name
        self.current_step += 1

    def get_progress(self) -> Dict:
        """Get current progress information."""
        if self.total_steps == 0:
            return {
                "percentage": 0,
                "current_step": 0,
                "total_steps": 0,
                "current_step_name": "",
                "elapsed_time": 0
            }

        percentage = min(
            100, int((self.current_step / self.total_steps) * 100))
        current_step_name = self.step_details[self.current_step -
                                              1] if self.current_step > 0 else ""
        elapsed_time = time.time() - self.start_time if self.start_time else 0

        return {
            "percentage": percentage,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "current_step_name": current_step_name,
            "elapsed_time": round(elapsed_time, 1)
        }


class BaseAIService(ABC):
    """Base class for AI service implementations."""

    def generate_image(self, prompt: str, current_image: str, user: User = None, post_data: dict = None, idea_content: str = None) -> str:
        """Generate an image for the given prompt. Should be implemented by subclasses."""
        raise NotImplementedError(
            "Image generation is not implemented for this provider.")

    def __init__(self, model_name: str = "default"):
        self.model_name = model_name
        self.progress_tracker = ProgressTracker()

    @abstractmethod
    def _validate_credits(self, user: User, estimated_tokens: int, model_name: str) -> bool:
        """Validate if user has sufficient credits."""
        pass

    @abstractmethod
    def _deduct_credits(self, user: User, actual_tokens: int, model_name: str, description: str) -> bool:
        """Deduct credits after AI operation."""
        pass

    @abstractmethod
    def _estimate_tokens(self, prompt: str, model_name: str) -> int:
        """Estimate token count for a prompt."""
        pass

    @abstractmethod
    def _make_ai_request(self, prompt: str, model_name: str, api_key: str = None, user: User = None, post_data: dict = None) -> str:
        """Make the actual AI API request."""
        pass

    def _build_creator_profile_section(self, profile: CreatorProfile) -> str:
        """Build creator profile section for the prompt with current model fields."""
        if not profile:
            return ""

        sections = []

        # Professional Information (Step 1)
        if profile.professional_name:
            sections.append(f"Nome Profissional: {profile.professional_name}")
        if profile.profession:
            sections.append(f"Profissão: {profile.profession}")
        if profile.instagram_handle:
            sections.append(f"Instagram Pessoal: @{profile.instagram_handle}")
        if profile.whatsapp_number:
            sections.append(f"WhatsApp: {profile.whatsapp_number}")

        # Business Information (Step 2)
        if profile.business_name:
            sections.append(f"Nome do Negócio: {profile.business_name}")
        if profile.specialization:
            sections.append(f"Especialização: {profile.specialization}")
        if profile.business_instagram_handle:
            sections.append(
                f"Instagram do Negócio: @{profile.business_instagram_handle}")
        if profile.business_website:
            sections.append(f"Website: {profile.business_website}")
        if profile.business_city and profile.business_city != "Remoto":
            sections.append(f"Localização: {profile.business_city}")
        if profile.business_description:
            sections.append(
                f"Descrição do Negócio: {profile.business_description}")

        # Branding Information (Step 3)
        if profile.voice_tone:
            sections.append(f"Tom de Voz Preferido: {profile.voice_tone}")

        # Color palette
        colors = [profile.color_1, profile.color_2,
                  profile.color_3, profile.color_4, profile.color_5]
        valid_colors = [color for color in colors if color and color.strip()]
        if valid_colors:
            sections.append(
                f"Paleta de Cores da Marca: {', '.join(valid_colors)}")

        if sections:
            return "PERFIL DO CRIADOR:\n" + "\n".join(f"- {section}" for section in sections)
        return ""

    def _normalize_content_type(self, raw_content_type: str, platform: str) -> str:
        """Normalize content type based on platform."""
        content_type_mapping = {
            'post': 'post',
            'story': 'story',
            'reel': 'reel',
            'video': 'video',
            'carousel': 'carousel',
            'live': 'live',
            'ad': 'ad',
            'tweet': 'post' if platform == 'twitter' else 'post',
            'thread': 'carousel' if platform == 'twitter' else 'post',
        }

        normalized = content_type_mapping.get(
            raw_content_type.lower(), raw_content_type.lower())

        # Platform-specific adjustments
        if platform == 'instagram' and normalized == 'tweet':
            normalized = 'post'
        elif platform == 'tiktok' and normalized in ['post', 'carousel']:
            normalized = 'video'

        return normalized

    def _parse_campaign_response(self, response_text: str, config: Dict) -> List[Dict]:
        """Parse AI response for campaign ideas."""
        try:
            # Try to extract JSON from response
            ideas_data = self._extract_multiple_json_objects(
                response_text, config)

            if not ideas_data:
                # Fallback to simple parsing
                ideas_data = self._create_fallback_ideas(config)

            return ideas_data

        except Exception:
            return self._create_fallback_ideas(config)
