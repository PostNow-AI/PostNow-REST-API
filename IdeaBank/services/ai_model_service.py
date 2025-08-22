from decimal import Decimal
from typing import Dict, List, Optional

from django.contrib.auth.models import User

try:
    from CreditSystem.models import AIModel
    from CreditSystem.services.credit_service import CreditService
    CREDIT_SYSTEM_AVAILABLE = True
except ImportError:
    CREDIT_SYSTEM_AVAILABLE = False
    CreditService = None
    AIModel = None


class AIModelService:
    """Service for managing AI model configurations and credit costs."""

    # Default model configurations if database is not available
    DEFAULT_MODELS = {
        'gemini-1.5-flash': {
            'provider': 'Google',
            'cost_per_token': Decimal('0.000001'),
            'max_tokens': 8192,
            'supports_streaming': False,
            'is_active': True
        },
        'gemini-1.5-pro': {
            'provider': 'Google',
            'cost_per_token': Decimal('0.000002'),
            'max_tokens': 32768,
            'supports_streaming': False,
            'is_active': True
        },
        'claude-3-sonnet': {
            'provider': 'Anthropic',
            'cost_per_token': Decimal('0.000003'),
            'max_tokens': 200000,
            'supports_streaming': True,
            'is_active': True
        },
        'gpt-4': {
            'provider': 'OpenAI',
            'cost_per_token': Decimal('0.00003'),
            'max_tokens': 8192,
            'supports_streaming': True,
            'is_active': True
        },
        'gpt-3.5-turbo': {
            'provider': 'OpenAI',
            'cost_per_token': Decimal('0.000002'),
            'max_tokens': 4096,
            'supports_streaming': True,
            'is_active': True
        }
    }

    @classmethod
    def get_available_models(cls) -> List[Dict]:
        """Get list of available AI models with their configurations."""
        if CREDIT_SYSTEM_AVAILABLE:
            try:
                db_models = AIModel.objects.filter(is_active=True)
                return [
                    {
                        'name': model.name,
                        'provider': model.provider,
                        'cost_per_token': float(model.cost_per_token),
                        'is_active': model.is_active
                    }
                    for model in db_models
                ]
            except Exception:
                pass

        # Fallback to default models
        return [
            {
                'name': name,
                'provider': config['provider'],
                'cost_per_token': float(config['cost_per_token']),
                'is_active': config['is_active']
            }
            for name, config in cls.DEFAULT_MODELS.items()
            if config['is_active']
        ]

    @classmethod
    def get_model_config(cls, model_name: str) -> Optional[Dict]:
        """Get configuration for a specific AI model."""
        if CREDIT_SYSTEM_AVAILABLE:
            try:
                model = AIModel.objects.get(name=model_name, is_active=True)
                return {
                    'name': model.name,
                    'provider': model.provider,
                    'cost_per_token': float(model.cost_per_token),
                    'is_active': model.is_active
                }
            except AIModel.DoesNotExist:
                pass

        # Fallback to default models
        return cls.DEFAULT_MODELS.get(model_name)

    @classmethod
    def calculate_cost(cls, model_name: str, estimated_tokens: int) -> float:
        """Calculate estimated cost for using a specific AI model."""
        model_config = cls.get_model_config(model_name)
        if not model_config:
            raise ValueError(f"Model '{model_name}' not found or not active")

        cost_per_token = model_config['cost_per_token']
        total_cost = cost_per_token * estimated_tokens

        return float(total_cost)

    @classmethod
    def validate_user_credits(cls, user: User, model_name: str, estimated_tokens: int) -> bool:
        """Validate if user has sufficient credits for the operation."""
        if not CREDIT_SYSTEM_AVAILABLE:
            return True  # Skip validation if credit system not available

        try:
            estimated_cost = cls.calculate_cost(model_name, estimated_tokens)
            return CreditService.has_sufficient_credits(user, estimated_cost)
        except Exception as e:
            print(f"Error validating credits: {str(e)}")
            return False

    @classmethod
    def deduct_credits(cls, user: User, model_name: str, actual_tokens: int, description: str = "") -> bool:
        """Deduct credits after successful AI operation."""
        if not CREDIT_SYSTEM_AVAILABLE:
            return True  # Skip deduction if credit system not available

        try:
            actual_cost = cls.calculate_cost(model_name, actual_tokens)
            return CreditService.deduct_credits(
                user=user,
                amount=actual_cost,
                ai_model=model_name,
                description=description
            )
        except Exception as e:
            print(f"Error deducting credits: {str(e)}")
            return False

    @classmethod
    def get_user_credit_balance(cls, user: User) -> float:
        """Get current credit balance for a user."""
        if not CREDIT_SYSTEM_AVAILABLE:
            return 0.0

        try:
            return CreditService.get_user_balance(user)
        except Exception:
            return 0.0

    @classmethod
    def estimate_tokens(cls, text: str, model_name: str = 'gemini-1.5-flash') -> int:
        """
        Estimate token count for text. This is a rough estimation.
        Different models may have different tokenization.
        """
        # Rough estimation: 1 token ≈ 4 characters for most languages
        # This is conservative and may overestimate
        estimated_tokens = len(text) // 4

        # Add buffer for response tokens (typically 2-3x input tokens)
        total_estimated = estimated_tokens * 3

        # Ensure minimum token count
        return max(total_estimated, 100)

    @classmethod
    def select_optimal_model(cls, user: User, estimated_tokens: int,
                             preferred_provider: str = None) -> Optional[str]:
        """
        Select the optimal AI model based on user credits and preferences.

        Args:
            user: User requesting the operation
            estimated_tokens: Estimated number of tokens needed
            preferred_provider: Preferred AI provider (optional)

        Returns:
            str: Name of the optimal model, or None if no suitable model found
        """
        available_models = cls.get_available_models()

        if not available_models:
            return None

        # Filter by preferred provider if specified
        if preferred_provider:
            available_models = [
                model for model in available_models
                if model['provider'].lower() == preferred_provider.lower()
            ]

        # Sort by cost (cheapest first)
        available_models.sort(key=lambda x: x['cost_per_token'])

        # Find the first model the user can afford
        for model in available_models:
            if cls.validate_user_credits(user, model['name'], estimated_tokens):
                return model['name']

        return None
