from decimal import Decimal
from typing import Dict, List, Optional

from django.contrib.auth.models import User

try:
    from CreditSystem.models import AIModel, AIModelPreferences, CreditTransaction
    from CreditSystem.services.credit_service import CreditService
    CREDIT_SYSTEM_AVAILABLE = True
except ImportError:
    CREDIT_SYSTEM_AVAILABLE = False
    CreditService = None
    AIModel = None
    AIModelPreferences = None
    CreditTransaction = None


class AIModelService:
    """Service for managing AI model configurations and credit costs."""

    # Default model configurations if database is not available
    # Only Gemini 2.5 Flash is supported
    DEFAULT_MODELS = {
        'gemini-2.5-flash': {
            'provider': 'Google',
            'cost_per_token': Decimal('0.008'),  # Reduced cost
            'max_tokens': 8192,
            'supports_streaming': False,
            'is_active': True
        }
    }

    @classmethod
    def get_available_models(cls) -> List[Dict]:
        """Get list of available AI models with their configurations. Only Gemini 2.5 Flash is supported."""
        # Force to return only Gemini 2.5 Flash regardless of database content
        return [
            {
                'name': 'gemini-2.5-flash',
                'provider': 'Google',
                'cost_per_token': float(cls.DEFAULT_MODELS['gemini-2.5-flash']['cost_per_token']),
                'is_active': True
            }
        ]

    @classmethod
    def get_model_config(cls, model_name: str) -> Optional[Dict]:
        """Get configuration for a specific AI model. Only Gemini 2.5 Flash is supported."""
        # Only return config for Gemini 2.5 Flash
        if model_name == 'gemini-2.5-flash':
            return cls.DEFAULT_MODELS.get(model_name)
        return None

    @classmethod
    def calculate_cost(cls, model_name: str, estimated_tokens: int) -> float:
        """Calculate estimated cost for using a specific AI model using FIXED PRICING."""
        if CREDIT_SYSTEM_AVAILABLE and CreditTransaction:
            # Use fixed pricing for text generation
            return float(CreditTransaction.get_fixed_price('text_generation'))

        # Fallback to fixed price if credit system not available
        return 0.02  # Fixed price for text generation

    @classmethod
    def calculate_image_cost(cls, model_name: str, num_images: int = 1) -> float:
        """Calculate estimated cost for image generation using FIXED PRICING."""
        if CREDIT_SYSTEM_AVAILABLE and CreditTransaction:
            # Use fixed pricing for image generation
            return float(CreditTransaction.get_fixed_price('image_generation')) * num_images

        # Fallback to fixed price if credit system not available
        return 0.23 * num_images  # Fixed price for image generation

    @classmethod
    def validate_user_credits(cls, user: User, model_name: str, estimated_tokens: int) -> bool:
        """Validate if user has sufficient credits and active subscription for text generation."""
        if not CREDIT_SYSTEM_AVAILABLE:
            return True  # Skip validation if credit system not available

        try:
            return CreditService.validate_operation(user, 'text_generation')
        except Exception:
            return False

    @classmethod
    def deduct_credits(cls, user: User, model_name: str, actual_tokens: int, description: str = "") -> bool:
        """Deduct credits after successful AI text generation using fixed pricing."""
        if not CREDIT_SYSTEM_AVAILABLE:
            return True  # Skip deduction if credit system not available

        try:
            return CreditService.deduct_credits_for_operation(
                user=user,
                operation_type='text_generation',
                ai_model=model_name,
                description=description or f"Text generation with {model_name}"
            )
        except Exception:
            return False

    @classmethod
    def validate_image_credits(cls, user: User, model_name: str, num_images: int = 1) -> bool:
        """Validate if user has sufficient credits and active subscription for image generation."""
        if not CREDIT_SYSTEM_AVAILABLE:
            return True  # Skip validation if credit system not available

        try:
            # For multiple images, check if user has enough credits for all
            if num_images > 1:
                if not CREDIT_SYSTEM_AVAILABLE or not CreditTransaction:
                    return True

                total_cost = CreditTransaction.get_fixed_price(
                    'image_generation') * num_images
                return CreditService.has_sufficient_credits(user, total_cost)
            else:
                return CreditService.validate_operation(user, 'image_generation')
        except Exception:
            return False

    @classmethod
    def deduct_image_credits(cls, user: User, model_name: str, num_images: int = 1, description: str = "") -> bool:
        """Deduct credits after successful image generation using fixed pricing."""
        if not CREDIT_SYSTEM_AVAILABLE:
            return True  # Skip deduction if credit system not available

        try:
            # For single image, use the operation method
            if num_images == 1:
                return CreditService.deduct_credits_for_operation(
                    user=user,
                    operation_type='image_generation',
                    ai_model=model_name,
                    description=description or f"Image generation with {model_name}"
                )
            else:
                # For multiple images, deduct the total amount
                total_cost = CreditTransaction.get_fixed_price(
                    'image_generation') * num_images
                return CreditService.deduct_credits(
                    user=user,
                    amount=total_cost,
                    ai_model=model_name,
                    description=f"Image generation ({num_images} images) with {model_name} - {description}" if description else f"Image generation ({num_images} images) with {model_name}"
                )
        except Exception:
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
    def estimate_tokens(cls, text: str, model_name: str = 'gemini-2.5-flash') -> int:
        """
        Estimate token count for text. This is a rough estimation.
        Only supports gemini-2.5-flash model.
        """
        # Only allow gemini-2.5-flash
        if model_name != 'gemini-2.5-flash':
            model_name = 'gemini-2.5-flash'

        # Rough estimation: 1 token ≈ 4 characters for most languages
        # This is conservative and may overestimate
        estimated_tokens = len(text) // 4

        # Add buffer for response tokens (typically 2-3x input tokens)
        total_estimated = estimated_tokens * 3

        # Ensure minimum token count
        return max(total_estimated, 100)

    @classmethod
    def select_optimal_model(cls, user: User, estimated_tokens: int,
                             operation_type: str = 'text_generation',
                             preferred_provider: str = None) -> Optional[str]:
        """
        Select the optimal AI model based on user preferences, credits, and operation requirements.

        Args:
            user: User requesting the operation
            estimated_tokens: Estimated number of tokens needed
            operation_type: Type of operation ('text_generation', 'creative', 'analysis', etc.)
            preferred_provider: Preferred AI provider (optional, overrides user preferences)

        Returns:
            str: Name of the optimal model, or None if no suitable model found
        """
        # Get user preferences
        user_prefs = cls.get_user_preferences(user)

        # Override provider if specified
        if preferred_provider:
            effective_provider = preferred_provider
        else:
            effective_provider = user_prefs.preferred_provider if user_prefs else 'auto'

        # Get budget preference
        budget_pref = user_prefs.budget_preference if user_prefs else 'balanced'
        max_cost = float(
            user_prefs.max_cost_per_operation) if user_prefs else 5.0

        # Check if user has a specific model preference for this operation type
        if user_prefs and user_prefs.preferred_models:
            specific_model = user_prefs.preferred_models.get(operation_type)
            if specific_model:
                # Validate the preferred model is available and affordable
                if cls.validate_user_credits(user, specific_model, estimated_tokens):
                    cost = cls.calculate_cost(specific_model, estimated_tokens)
                    if cost <= max_cost:
                        return specific_model
                elif user_prefs.allow_fallback:
                    # Continue to automatic selection
                    pass
                else:
                    # User doesn't want fallback, return None
                    return None

        # Get available models
        available_models = cls.get_available_models()
        if not available_models:
            return None

        # Filter by provider preference if not 'auto'
        if effective_provider != 'auto':
            available_models = [
                model for model in available_models
                if model['provider'].lower() == effective_provider.lower()
            ]

            if not available_models:
                # No models available for preferred provider
                if user_prefs and user_prefs.allow_fallback:
                    # Reset to all models for fallback
                    available_models = cls.get_available_models()
                else:
                    return None

        # Filter models by budget constraints
        affordable_models = []
        for model in available_models:
            if cls.validate_user_credits(user, model['name'], estimated_tokens):
                cost = cls.calculate_cost(model['name'], estimated_tokens)
                if cost <= max_cost:
                    affordable_models.append({
                        **model,
                        'estimated_cost': cost,
                        'cost_per_token': model['cost_per_token']
                    })

        if not affordable_models:
            return None

        # Select model based on budget preference
        if budget_pref == 'economy':
            # Always choose the cheapest
            selected = min(affordable_models,
                           key=lambda x: x['estimated_cost'])
        elif budget_pref == 'performance':
            # Choose the most expensive (assuming higher cost = better quality)
            selected = max(affordable_models,
                           key=lambda x: x['estimated_cost'])
        else:  # balanced or custom
            # Sort by cost-effectiveness (balance between cost and assumed quality)
            # Assign quality scores based on model characteristics
            for model in affordable_models:
                model['quality_score'] = cls._get_model_quality_score(
                    model['name'])
                model['value_score'] = model['quality_score'] / \
                    max(model['estimated_cost'], 0.001)

            selected = max(affordable_models, key=lambda x: x['value_score'])

        return selected['name']

    @classmethod
    def _get_model_quality_score(cls, model_name: str) -> float:
        """
        Assign quality scores to models based on their capabilities.
        Higher score = better quality.
        """
        quality_scores = {
            # Google Gemini - Only supported model
            'gemini-2.5-flash': 8.0,  # High quality score for our primary model
        }

        # Default score for unknown models
        return quality_scores.get(model_name, 5.0)

    @classmethod
    def get_user_preferences(cls, user: User):
        """Get or create user AI preferences."""
        if not CREDIT_SYSTEM_AVAILABLE:
            return None

        try:
            preferences, created = AIModelPreferences.objects.get_or_create(
                user=user,
                defaults={
                    'preferred_provider': 'auto',
                    'budget_preference': 'balanced',
                    'max_cost_per_operation': Decimal('5.00'),
                    'auto_select_cheapest': True,
                    'allow_fallback': True,
                }
            )
            return preferences
        except Exception:
            return None

    @classmethod
    def update_user_preferences(cls, user: User, preferences_data: Dict) -> bool:
        """Update user AI model preferences."""
        if not CREDIT_SYSTEM_AVAILABLE:
            return False

        try:
            preferences = cls.get_user_preferences(user)
            if not preferences:
                return False

            # Update allowed fields
            allowed_fields = [
                'preferred_provider', 'budget_preference', 'max_cost_per_operation',
                'preferred_models', 'auto_select_cheapest', 'allow_fallback'
            ]

            for field in allowed_fields:
                if field in preferences_data:
                    setattr(preferences, field, preferences_data[field])

            preferences.save()
            return True
        except Exception:
            return False

    @classmethod
    def get_model_recommendations(cls, user: User, operation_type: str = 'text_generation') -> List[Dict]:
        """
        Get model recommendations for a user based on their preferences and budget.

        Returns a list of recommended models with reasons.
        """
        recommendations = []
        user_prefs = cls.get_user_preferences(user)
        available_models = cls.get_available_models()

        if not available_models:
            return recommendations

        user_balance = cls.get_user_credit_balance(user)
        max_cost = float(
            user_prefs.max_cost_per_operation) if user_prefs else 5.0

        for model in available_models:
            # Estimate cost for a typical operation (1000 tokens)
            estimated_cost = model['cost_per_token'] * 1000

            if estimated_cost <= max_cost and estimated_cost <= user_balance:
                quality_score = cls._get_model_quality_score(model['name'])
                value_score = quality_score / max(estimated_cost, 0.001)

                reason = []
                if estimated_cost <= max_cost * 0.3:
                    reason.append("Muito econômico")
                elif estimated_cost <= max_cost * 0.7:
                    reason.append("Custo moderado")
                else:
                    reason.append("Premium")

                if quality_score >= 8.5:
                    reason.append("Alta qualidade")
                elif quality_score >= 7.0:
                    reason.append("Boa qualidade")

                recommendations.append({
                    'model_name': model['name'],
                    'provider': model['provider'],
                    'estimated_cost': estimated_cost,
                    'quality_score': quality_score,
                    'value_score': value_score,
                    'reasons': reason,
                    'is_recommended': value_score > 1.0
                })

        # Sort by value score
        recommendations.sort(key=lambda x: x['value_score'], reverse=True)
        return recommendations
