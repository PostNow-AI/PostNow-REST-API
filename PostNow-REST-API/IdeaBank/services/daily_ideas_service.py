"""
Daily Ideas Service - Generates daily content ideas for users.
Refactored to follow SOLID principles.
"""
import logging
from typing import Any, Dict, Optional

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.db import connection
from django.utils import timezone
from google.genai import types

from AuditSystem.services import AuditService
from ClientContext.models import ClientContext
from ClientContext.serializers import ClientContextSerializer
from ClientContext.utils.json_helpers import clean_json_string, safe_json_loads
from CreatorProfile.models import CreatorProfile
from IdeaBank.models import Post, PostIdea
from Analytics.services.image_pregen_policy import (
    ACTION_PRE_GENERATE,
    make_image_pregen_decision,
)
from Analytics.services.text_variant_policy import make_text_variant_decision
from services.ai_prompt_service import AIPromptService
from services.ai_service import AiService
from services.s3_sevice import S3Service
from services.semaphore_service import SemaphoreService
from services.user_validation_service import UserValidationService

logger = logging.getLogger(__name__)

# Constants
MAX_WEEKLY_ITERATIONS = 7
ITERATIONS_PER_EXECUTION = 2


class DailyIdeasService:
    """
    Service for generating daily content ideas for users.

    Responsibilities:
    - Orchestrate daily ideas generation
    - Process users in batches
    - Track weekly progress
    """

    def __init__(
        self,
        user_validation_service: Optional[UserValidationService] = None,
        semaphore_service: Optional[SemaphoreService] = None,
        ai_service: Optional[AiService] = None,
        prompt_service: Optional[AIPromptService] = None,
        audit_service: Optional[AuditService] = None,
        s3_service: Optional[S3Service] = None,
    ):
        """Initialize with optional dependency injection."""
        self.user_validation_service = user_validation_service or UserValidationService()
        self.semaphore_service = semaphore_service or SemaphoreService()
        self.ai_service = ai_service or AiService()
        self.prompt_service = prompt_service or AIPromptService()
        self.audit_service = audit_service or AuditService()
        self.s3_service = s3_service or S3Service()

    # Public API

    async def process_daily_ideas_for_users(
        self,
        batch_number: int,
        batch_size: int
    ) -> Dict[str, Any]:
        """Process daily ideas generation for a batch of users."""
        start_time = timezone.now()
        target_week = start_time.strftime("%Y-W%W")

        offset, limit = self._calculate_pagination(batch_number, batch_size)
        eligible_users = await self._get_eligible_users(offset, limit, target_week)
        total = len(eligible_users)

        if total > 0:
            await self._log_batch_telemetry(batch_number, batch_size, total, target_week)

        if total == 0:
            return self._empty_result("No eligible users found")

        try:
            results = await self.semaphore_service.process_concurrently(
                users=eligible_users,
                function=self.process_single_user
            )
            return self._build_results(results, total, start_time)

        except Exception as e:
            return self._error_result(total, str(e))

    async def process_single_user(self, user_data: dict) -> Dict[str, Any]:
        """Process daily ideas generation for a single user."""
        user_id = user_data.get("id") or user_data.get("user_id")

        if not user_data:
            return {"status": "failed", "reason": "no_user_data"}
        if not user_id:
            return {"status": "failed", "reason": "no_user_id", "user_data": user_data}

        return await self._process_user_daily_ideas(user_id)

    # Private - User Processing

    async def _process_user_daily_ideas(self, user_id: int) -> Dict[str, Any]:
        """Generate daily ideas for a user - processes up to 2 iterations per execution."""
        user = await sync_to_async(User.objects.get)(id=user_id)
        current_week = timezone.now().strftime("%Y-W%W")

        try:
            # Validate user
            validation_result = await self._validate_user_for_processing(user_id)
            if validation_result:
                return validation_result

            # Get and check progress
            current_progress = await self._get_user_progress(user_id, current_week)
            iterations_to_process = min(
                ITERATIONS_PER_EXECUTION,
                MAX_WEEKLY_ITERATIONS - current_progress
            )

            if iterations_to_process <= 0:
                return self._skipped_result(
                    user_id, "weekly_content_complete", f"{MAX_WEEKLY_ITERATIONS}/{MAX_WEEKLY_ITERATIONS}"
                )

            await self._log_audit(user, "daily_content_generation_started", "info")

            # Process iterations
            user_posts, current_progress = await self._process_iterations(
                user, iterations_to_process, current_progress, current_week
            )

            await self._clear_user_error(user)
            final_status = "success" if current_progress >= MAX_WEEKLY_ITERATIONS else "partial"

            return {
                "status": final_status,
                "user_id": user_id,
                "created_posts": user_posts,
                "progress": f"{current_progress}/{MAX_WEEKLY_ITERATIONS}",
            }

        except Exception as e:
            await self._store_user_error(user, str(e))
            await self._log_audit(
                user, "daily_content_generation_failed", "error", {"error": str(e)}
            )
            return {"status": "failed", "error": str(e), "user_id": user_id}

    async def _process_iterations(
        self,
        user: User,
        iterations_to_process: int,
        current_progress: int,
        current_week: str
    ) -> tuple[list, int]:
        """Process content generation iterations."""
        user_posts = []

        for iteration in range(iterations_to_process):
            try:
                content_result = await sync_to_async(self._generate_content_for_user)(user)
                content_loaded = safe_json_loads(clean_json_string(content_result))

                # Save all post types
                await self._save_all_post_types(user, content_loaded, user_posts)

                # Update progress
                current_progress += 1
                await self._update_user_progress(user, current_progress, current_week)

            except Exception as iteration_error:
                await self._log_audit(
                    user, "iteration_failed", "error",
                    {"error": str(iteration_error), "iteration": iteration + 1}
                )
                if iteration == 0:
                    raise iteration_error
                break

        return user_posts, current_progress

    async def _save_all_post_types(
        self,
        user: User,
        content_loaded: dict,
        user_posts: list
    ):
        """Save all post types from generated content."""
        post_configs = [
            ("feed", content_loaded.get("post_text_feed", {})),
            ("story", content_loaded.get("post_text_stories", {})),
            ("reels", content_loaded.get("post_text_reels", {})),
        ]

        for post_type, post_data in post_configs:
            post_content = self._format_post_content(post_data, post_type)
            await self._save_text_to_db(user, post_data, post_content, user_posts, post_type)

    def _format_post_content(self, post_data: dict, post_type: str) -> str:
        """Format post content based on type (DRY helper)."""
        hashtags = ' '.join(post_data.get('hashtags', []))
        cta = post_data.get('cta', '').strip()

        if post_type == "feed":
            legenda = post_data.get('legenda', '').strip()
            return f"{legenda}\n\n\n{hashtags}\n\n\n{cta}"

        elif post_type == "story":
            roteiro = post_data.get('roteiro', '').strip()
            return f"{roteiro}\n\n\n{hashtags}\n\n\n{cta}"

        else:  # reels
            roteiro = post_data.get('roteiro', '').strip()
            legenda = post_data.get('legenda', '').strip()
            return f"{roteiro}\n\n\n{legenda}\n\n\n{hashtags}\n\n\n{cta}"

    # Private - Database Operations

    @sync_to_async
    def _get_eligible_users(
        self,
        offset: int,
        limit: Optional[int],
        target_week: str
    ) -> list[dict[str, Any]]:
        """Get a batch of users eligible for daily content generation."""
        cursor = connection.cursor()

        base_query = """
            SELECT DISTINCT u.id, u.email, u.username,
                   u.weekly_generation_progress, u.weekly_generation_week
            FROM auth_user u
            INNER JOIN CreditSystem_usersubscription us ON us.user_id = u.id
            WHERE u.daily_generation_error IS NULL
              AND u.is_active = 1
              AND us.status = 'active'
              AND (u.weekly_generation_week != %s
                   OR u.weekly_generation_week IS NULL
                   OR u.weekly_generation_progress < 7)
        """

        if limit is None:
            query = base_query + " LIMIT 999999 OFFSET %s"
            cursor.execute(query, [target_week, offset])
        else:
            query = base_query + " LIMIT %s OFFSET %s"
            cursor.execute(query, [target_week, limit, offset])

        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    async def _save_text_to_db(
        self,
        user: User,
        post_data: dict,
        post_content: str,
        user_posts: list,
        post_type: str,
    ):
        """Save generated text content to database."""
        sugestao_visual = post_data.get("sugestao_visual", "")

        post = await sync_to_async(Post.objects.create)(
            user=user,
            name=post_data.get("titulo", "Conteúdo Diário"),
            type=post_type,
            further_details="",
            include_image=post_type == "feed",
            is_automatically_generated=True,
            is_active=False,
        )

        post_idea = await sync_to_async(PostIdea.objects.create)(
            post=post,
            content=post_content,
            image_url="",
            image_description=sugestao_visual,
        )

        # Telemetry
        await self._log_text_variant_telemetry(user, post_idea, post_type)

        # Generate image for feed posts
        if post_type == "feed":
            await self._maybe_generate_image(user, post_idea, post_content, post_type)

        user_posts.append({
            "post_id": post_idea.id,
            "post_idea_id": post_idea.id,
            "type": post.type,
            "title": post.name,
        })

    async def _maybe_generate_image(
        self,
        user: User,
        post_idea: PostIdea,
        post_content: str,
        post_type: str
    ):
        """Generate image if policy allows."""
        decision = await sync_to_async(make_image_pregen_decision)(
            user, "PostIdea", str(post_idea.id),
            {"post_type": post_type, "objective": "unknown", "source": "daily_generation"}
        )

        if decision.action == ACTION_PRE_GENERATE:
            image_url = await sync_to_async(self._generate_image_for_feed_post)(
                user, post_content
            )
            post_idea.image_url = image_url
            await sync_to_async(post_idea.save)()

    # Private - AI Generation

    def _generate_content_for_user(self, user: User) -> str:
        """Generate daily content using AI."""
        try:
            self.prompt_service.set_user(user)
            context = ClientContext.objects.filter(user=user).first()
            serializer = ClientContextSerializer(context)
            context_data = serializer.data if serializer else {}

            prompt = self.prompt_service.build_campaign_prompts(context_data)
            return self.ai_service.generate_text(
                prompt, user,
                types.GenerateContentConfig(
                    temperature=0.7, top_p=0.9,
                    response_modalities=["TEXT"]
                )
            )
        except Exception as e:
            raise Exception(f"Failed to generate context for user {user.id}: {str(e)}")

    def _generate_image_for_feed_post(self, user: User, post_content: str) -> str:
        """Generate image for feed post using AI."""
        try:
            user_logo = self._get_user_logo(user)
            self.prompt_service.set_user(user)

            # Semantic analysis
            semantic_result = self.ai_service.generate_text(
                self.prompt_service.semantic_analysis_prompt(post_content), user
            )
            semantic_loaded = safe_json_loads(clean_json_string(semantic_result))

            # Adapted semantic analysis
            adapted_result = self.ai_service.generate_text(
                self.prompt_service.adapted_semantic_analysis_prompt(semantic_loaded), user
            )
            adapted_loaded = safe_json_loads(clean_json_string(adapted_result))
            semantic_analysis = adapted_loaded.get("analise_semantica", {})

            # Generate image
            image_prompt = self.prompt_service.image_generation_prompt(semantic_analysis)
            image_result = self.ai_service.generate_image(
                image_prompt, user_logo, user,
                types.GenerateContentConfig(
                    temperature=0.7, top_p=0.9,
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio="4:5")
                )
            )

            return self.s3_service.upload_image(user, image_result) if image_result else ""

        except Exception as e:
            raise Exception(f"Failed to generate image for user {user.id}: {str(e)}")

    def _get_user_logo(self, user: User) -> str:
        """Get user logo, extracting base64 if needed."""
        profile = CreatorProfile.objects.filter(user=user).first()
        if not profile or not profile.logo:
            return ""

        logo = profile.logo
        if "data:image/" in logo and ";base64," in logo:
            return logo.split(",")[1]
        return logo

    # Private - Progress & Error Management

    async def _get_user_progress(self, user_id: int, current_week: str) -> int:
        """Get user's current weekly progress."""
        def get_progress():
            cursor = connection.cursor()
            cursor.execute(
                "SELECT weekly_generation_progress, weekly_generation_week FROM auth_user WHERE id = %s",
                [user_id]
            )
            row = cursor.fetchone()
            if row:
                return {"progress": row[0], "week": row[1]}
            return {"progress": 0, "week": None}

        progress_data = await sync_to_async(get_progress)()
        progress = progress_data.get("progress") or 0

        # Reset if new week
        if progress_data.get("week") != current_week:
            return 0
        return progress

    @staticmethod
    async def _update_user_progress(user: User, progress: int, week: str):
        """Update user's weekly generation progress."""
        await sync_to_async(
            lambda: connection.cursor().execute(
                "UPDATE auth_user SET weekly_generation_progress = %s, weekly_generation_week = %s WHERE id = %s",
                [progress, week, user.id]
            )
        )()

    @staticmethod
    async def _store_user_error(user: User, error_message: str):
        """Store error message for retry processing."""
        await sync_to_async(
            lambda: connection.cursor().execute(
                "UPDATE auth_user SET daily_generation_error = %s, daily_generation_error_date = %s WHERE id = %s",
                [error_message, timezone.now(), user.id]
            )
        )()

    @staticmethod
    async def _clear_user_error(user: User):
        """Clear error after successful generation."""
        await sync_to_async(
            lambda: connection.cursor().execute(
                "UPDATE auth_user SET daily_generation_error = NULL, daily_generation_error_date = NULL WHERE id = %s",
                [user.id]
            )
        )()

    # Private - Validation & Helpers

    async def _validate_user_for_processing(self, user_id: int) -> Optional[Dict]:
        """Validate user eligibility. Returns error dict if invalid, None if valid."""
        user_data = await self.user_validation_service.get_user_data(user_id)
        if not user_data:
            return {"status": "failed", "reason": "user_not_found", "user_id": user_id}

        validation_result = await self.user_validation_service.validate_user_eligibility(user_data)
        if validation_result["status"] != "eligible":
            return {"status": "skipped", "reason": validation_result["reason"], "user_id": user_id}

        return None

    def _calculate_pagination(self, batch_number: int, batch_size: int) -> tuple[int, Optional[int]]:
        """Calculate offset and limit for pagination."""
        if batch_size == 0:
            return 0, None
        return (batch_number - 1) * batch_size, batch_size

    # Private - Telemetry & Logging

    async def _log_audit(
        self,
        user: User,
        action: str,
        status: str,
        details: Optional[dict] = None
    ):
        """Log audit event."""
        kwargs = {"user": user, "action": action, "status": status}
        if details:
            kwargs["details"] = details
        await sync_to_async(self.audit_service.log_daily_content_generation)(**kwargs)

    async def _log_text_variant_telemetry(self, user: User, post_idea: PostIdea, post_type: str):
        """Log text variant telemetry."""
        try:
            await sync_to_async(make_text_variant_decision)(
                user, "PostIdea", str(post_idea.id),
                {"post_type": post_type, "objective": "unknown", "source": "daily_generation"}
            )
        except Exception:
            pass

    async def _log_batch_telemetry(
        self,
        batch_number: int,
        batch_size: int,
        total: int,
        target_week: str
    ):
        """Log batch scheduling telemetry."""
        try:
            from Analytics.models import Decision
            await sync_to_async(Decision.objects.create)(
                decision_type="scheduler_batch",
                action="daily_generation",
                policy_id="scheduler_fixed_v0",
                user=None,
                resource_type="Batch",
                resource_id=f"daily:{target_week}:{batch_number}",
                context={"batch_number": batch_number, "batch_size": batch_size, "users": total},
                properties={},
            )
        except Exception:
            pass

    # Private - Result Builders

    def _build_results(
        self,
        results: list,
        total: int,
        start_time
    ) -> Dict[str, Any]:
        """Build the final results dictionary."""
        end_time = timezone.now()
        return {
            "status": "completed",
            "processed": sum(1 for r in results if r.get("status") == "success"),
            "partial": sum(1 for r in results if r.get("status") == "partial"),
            "created_posts": sum(
                len(r.get("created_posts", []))
                for r in results if r.get("status") in ["success", "partial"]
            ),
            "failed": sum(1 for r in results if r.get("status") == "failed"),
            "skipped": sum(1 for r in results if r.get("status") == "skipped"),
            "total_users": total,
            "duration_seconds": (end_time - start_time).total_seconds(),
            "details": results,
        }

    def _empty_result(self, message: str) -> Dict[str, Any]:
        return {"status": "completed", "processed": 0, "total_users": 0, "message": message}

    def _error_result(self, total: int, error: str) -> Dict[str, Any]:
        return {"status": "error", "processed": 0, "total_users": total, "message": f"Error processing users: {error}"}

    def _skipped_result(self, user_id: int, reason: str, progress: str) -> Dict[str, Any]:
        return {"status": "skipped", "reason": reason, "user_id": user_id, "progress": progress}
