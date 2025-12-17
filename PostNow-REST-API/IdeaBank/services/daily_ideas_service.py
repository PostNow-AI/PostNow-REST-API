import json
import logging
from typing import Any, Dict

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.db import connection
from django.utils import timezone
from google.genai import types

from AuditSystem.services import AuditService
from ClientContext.models import ClientContext
from ClientContext.serializers import ClientContextSerializer
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


class DailyIdeasService:
    def __init__(self):
        self.user_validation_service = UserValidationService()
        self.semaphore_service = SemaphoreService()
        self.ai_service = AiService()
        self.prompt_service = AIPromptService()
        self.audit_service = AuditService()
        self.s3_service = S3Service()

    @sync_to_async
    def _get_eligible_users(
        self, offset: int, limit: int, target_week: str
    ) -> list[dict[str, Any]]:
        """Get a batch of users eligible for weekly context generation"""

        cursor = connection.cursor()

        # Build SQL query with subquery for active subscriptions
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
            # MySQL requires LIMIT when using OFFSET, use very large number for "all"
            query = base_query + " LIMIT 999999 OFFSET %s"
            cursor.execute(query, [target_week, offset])
        else:
            query = base_query + " LIMIT %s OFFSET %s"
            cursor.execute(query, [target_week, limit, offset])

        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return results

    async def process_daily_ideas_for_users(
        self, batch_number: int, batch_size: int
    ) -> Dict[str, Any]:
        """Process daily ideas generation for a batch of users"""
        start_time = timezone.now()
        offset = (batch_number - 1) * batch_size
        limit = batch_size

        if batch_size == 0:
            offset = 0
            limit = None  # Process all users

        # Calculate current week in format YYYY-Www (e.g., "2025-W50")
        target_week = start_time.strftime("%Y-W%W")

        eligible_users = await self._get_eligible_users(
            offset=offset, limit=limit, target_week=target_week
        )
        total = len(eligible_users)

        if total > 0:
            # Telemetria de agendamento (base pronta p/ RL de retries/scheduling)
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

        if total == 0:
            return {
                "status": "completed",
                "processed": 0,
                "total_users": 0,
                "message": "No eligible users found",
            }

        try:
            results = await self.semaphore_service.process_concurrently(
                users=eligible_users, function=self.process_single_user
            )

            processed_count = sum(1 for r in results if r.get("status") == "success")
            partial_count = sum(1 for r in results if r.get("status") == "partial")
            failed_count = sum(1 for r in results if r.get("status") == "failed")
            skipped_count = sum(1 for r in results if r.get("status") == "skipped")
            created_posts_count = sum(
                len(r.get("created_posts", []))
                for r in results
                if r.get("status") in ["success", "partial"]
            )

            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                "status": "completed",
                "processed": processed_count,
                "partial": partial_count,
                "created_posts": created_posts_count,
                "failed": failed_count,
                "skipped": skipped_count,
                "total_users": total,
                "duration_seconds": duration,
                "details": results,
            }

            return result
        except Exception as e:
            return {
                "status": "error",
                "processed": 0,
                "total_users": total,
                "message": f"Error processing users: {str(e)}",
            }

    async def process_single_user(self, user_data: dict) -> Dict[str, Any]:
        """Process daily ideas generation for a single user"""
        user_id = user_data.get("id") or user_data.get("user_id")
        if not user_data:
            return {"status": "failed", "reason": "no_user_data"}
        if not user_id:
            return {"status": "failed", "reason": "no_user_id", "user_data": user_data}

        return await self._process_user_daily_ideas(user_id)

    async def _process_user_daily_ideas(self, user_id: int) -> Dict[str, Any]:
        """Generate daily ideas to the user - processes 2 iterations per execution"""
        user = await sync_to_async(User.objects.get)(id=user_id)
        current_week = timezone.now().strftime("%Y-W%W")

        try:
            # Get current progress from database
            user_data = await self.user_validation_service.get_user_data(user_id)
            if not user_data:
                return {
                    "status": "failed",
                    "reason": "user_not_found",
                    "user_id": user_id,
                }

            # Get current progress using raw SQL
            def get_progress():
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT weekly_generation_progress, weekly_generation_week FROM auth_user WHERE id = %s",
                    [user_id],
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "weekly_generation_progress": row[0],
                        "weekly_generation_week": row[1],
                    }
                return {"weekly_generation_progress": 0, "weekly_generation_week": None}

            progress = await sync_to_async(get_progress)()

            current_progress = progress.get("weekly_generation_progress") or 0
            stored_week = progress.get("weekly_generation_week")

            # Reset progress if it's a new week
            if stored_week != current_week:
                current_progress = 0

            # Calculate how many iterations to process (max 2, but don't exceed 7 total)
            iterations_to_process = min(2, 7 - current_progress)

            if iterations_to_process <= 0:
                return {
                    "status": "skipped",
                    "reason": "weekly_content_complete",
                    "user_id": user_id,
                    "progress": "7/7",
                }

            await sync_to_async(self.audit_service.log_daily_content_generation)(
                user=user,
                action="daily_content_generation_started",
                status="info",
            )

            validation_result = (
                await self.user_validation_service.validate_user_eligibility(user_data)
            )

            if validation_result["status"] != "eligible":
                return {
                    "status": "skipped",
                    "reason": validation_result["reason"],
                    "user_id": user_id,
                }

            user_posts = []

            # Process iterations (up to 2 per execution)
            for iteration in range(iterations_to_process):
                try:
                    content_result = await sync_to_async(
                        self._generate_content_for_user
                    )(user)

                    content_json = (
                        content_result.replace("json", "", 1).strip("`").strip()
                    )
                    content_loaded = json.loads(content_json)

                    post_text_feed = content_loaded.get("post_text_feed")
                    post_text_stories = content_loaded.get("post_text_stories")
                    post_text_reels = content_loaded.get("post_text_reels")

                    post_content_feed = f"""{post_text_feed.get('legenda', '').strip()}\n\n\n{' '.join(post_text_feed.get('hashtags', []))}\n\n\n{post_text_feed.get('cta', '').strip()}
                    """

                    post_content_stories = f"""{post_text_stories.get('roteiro', '').strip()}\n\n\n{' '.join(post_text_stories.get('hashtags', []))}\n\n\n{post_text_stories.get('cta', '').strip()}
                    """

                    post_content_reels = f"""{post_text_reels.get('roteiro', '').strip()}\n\n\n{post_text_reels.get('legenda', '').strip()}\n\n\n{' '.join(post_text_reels.get('hashtags', []))}\n\n\n{post_text_reels.get('cta', '').strip()}
                    """

                    await self._save_text_to_db(
                        user, post_text_feed, post_content_feed, user_posts, "feed"
                    )
                    await self._save_text_to_db(
                        user,
                        post_text_stories,
                        post_content_stories,
                        user_posts,
                        "story",
                    )
                    await self._save_text_to_db(
                        user, post_text_reels, post_content_reels, user_posts, "reels"
                    )

                    # Update progress after successful iteration
                    current_progress += 1
                    await self._update_user_progress(
                        user, current_progress, current_week
                    )

                except Exception as iteration_error:
                    # Log iteration failure but continue if we have at least one success
                    await sync_to_async(
                        self.audit_service.log_daily_content_generation
                    )(
                        user=user,
                        action="iteration_failed",
                        details={
                            "error": str(iteration_error),
                            "iteration": iteration + 1,
                        },
                    )
                    if iteration == 0:
                        # If first iteration fails, raise the error
                        raise iteration_error
                    # If second iteration fails, we still have one success
                    break

            await self._clear_user_error(user)

            # Determine final status
            final_status = "success" if current_progress >= 7 else "partial"

            return {
                "status": final_status,
                "user_id": user_id,
                "created_posts": user_posts,
                "progress": f"{current_progress}/7",
            }
        except Exception as e:
            await self._store_user_error(user, str(e))
            await sync_to_async(self.audit_service.log_daily_content_generation)(
                user=user,
                action="daily_content_generation_failed",
                details={"error": str(e)},
            )
            return {"status": "failed", "error": str(e), "user_id": user_id}

    async def _save_text_to_db(
        self,
        user: User,
        post_data: dict,
        post_content: str,
        user_posts: list,
        post_type: str,
    ) -> None:
        sugestao_visual = post_data.get("sugestao_visual", "")

        post = await sync_to_async(Post.objects.create)(
            user=user,
            name=post_data.get("titulo", "Conteúdo Diário"),
            type=post_type,
            further_details="",
            include_image=True if post_type == "feed" else False,
            is_automatically_generated=True,
            is_active=False,
        )

        post_idea = await sync_to_async(PostIdea.objects.create)(
            post=post,
            content=post_content,
            image_url="",
            image_description=sugestao_visual,
        )

        # Telemetria de variante de texto (base p/ bandit futuro, sem alterar comportamento)
        try:
            await sync_to_async(make_text_variant_decision)(
                user,
                "PostIdea",
                str(post_idea.id),
                {
                    "post_type": post_type,
                    "objective": "unknown",
                    "source": "daily_generation",
                },
            )
        except Exception:
            pass

        if post_type == "feed":
            decision = await sync_to_async(make_image_pregen_decision)(
                user,
                "PostIdea",
                str(post_idea.id),
                {
                    "post_type": post_type,
                    "objective": "unknown",
                    "source": "daily_generation",
                },
            )

            if decision.action == ACTION_PRE_GENERATE:
                image_url = await sync_to_async(self._generate_image_for_feed_post)(
                    user, post_content
                )
                post_idea.image_url = image_url
                await sync_to_async(post_idea.save)()

        user_posts.append(
            {
                "post_id": post_idea.id,
                "post_idea_id": post_idea.id,
                "type": post.type,
                "title": post.name,
            }
        )

    def _generate_image_for_feed_post(self, user: User, post_content: str) -> str:
        """AI service call to generate image for feed post."""
        # TODO: Fix image gen config to better one
        try:
            user_logo = CreatorProfile.objects.filter(user=user).first().logo

            if user_logo and "data:image/" in user_logo and ";base64," in user_logo:
                user_logo = user_logo.split(",")[1]

            image_url = ""
            self.prompt_service.set_user(user)

            semantic_prompt = self.prompt_service.semantic_analysis_prompt(post_content)
            semantic_result = self.ai_service.generate_text(semantic_prompt, user)
            semantic_json = semantic_result.replace("json", "", 1).strip("`").strip()
            semantic_loaded = json.loads(semantic_json)

            adapted_semantic_analysis_prompt = (
                self.prompt_service.adapted_semantic_analysis_prompt(semantic_loaded)
            )

            adapted_semantic_json = self.ai_service.generate_text(
                adapted_semantic_analysis_prompt, user
            )
            adapted_semantic_str = (
                adapted_semantic_json.replace("json", "", 1).strip("`").strip()
            )
            adapted_semantic_loaded = json.loads(adapted_semantic_str)

            semantic_analysis = adapted_semantic_loaded.get("analise_semantica", {})

            image_prompt = self.prompt_service.image_generation_prompt(
                semantic_analysis
            )

            # image_generated_prompt = self.ai_service.generate_text(
            #     image_prompt, user)

            # print(image_generated_prompt)

            image_result = self.ai_service.generate_image(
                image_prompt,
                user_logo,
                user,
                types.GenerateContentConfig(
                    temperature=0.7,
                    top_p=0.9,
                    response_modalities=[
                        "IMAGE",
                    ],
                    image_config=types.ImageConfig(
                        aspect_ratio="4:5",
                    ),
                ),
            )

            if not image_result:
                image_url = ""
            else:
                image_url = self.s3_service.upload_image(user, image_result)

            return image_url
        except Exception as e:
            raise Exception(f"Failed to generate image for user {user.id}: {str(e)}")

    def _generate_content_for_user(self, user: User) -> str:
        """AI service call to generate daily ideas for a user."""
        try:
            self.prompt_service.set_user(user)
            context = ClientContext.objects.filter(user=user).first()
            serializer = ClientContextSerializer(context)

            context_data = serializer.data if serializer else {}

            prompt = self.prompt_service.build_campaign_prompts(context_data)

            content_result = self.ai_service.generate_text(
                prompt,
                user,
                types.GenerateContentConfig(
                    temperature=0.7,
                    top_p=0.9,
                    response_modalities=[
                        "TEXT",
                    ],
                ),
            )

            return content_result
        except Exception as e:
            raise Exception(f"Failed to generate context for user {user.id}: {str(e)}")

    @staticmethod
    async def _store_user_error(user, error_message: str):
        """Store error message in user model for retry processing."""
        await sync_to_async(
            lambda: connection.cursor().execute(
                "UPDATE auth_user SET daily_generation_error = %s, daily_generation_error_date = %s WHERE id = %s",
                [error_message, timezone.now(), user.id],
            )
        )()

    @staticmethod
    async def _clear_user_error(user):
        """Clear error message from user model after successful generation."""
        await sync_to_async(
            lambda: connection.cursor().execute(
                "UPDATE auth_user SET daily_generation_error = NULL, daily_generation_error_date = NULL WHERE id = %s",
                [user.id],
            )
        )()

    @staticmethod
    async def _update_user_progress(user, progress: int, week: str):
        """Update user's weekly generation progress."""
        await sync_to_async(
            lambda: connection.cursor().execute(
                "UPDATE auth_user SET weekly_generation_progress = %s, weekly_generation_week = %s WHERE id = %s",
                [progress, week, user.id],
            )
        )()
