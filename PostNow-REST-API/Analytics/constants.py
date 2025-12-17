from __future__ import annotations


class AnalyticsEventName:
    """
    Mantemos como constantes (e não enum do Django) para:
    - evitar migrações por mudança de choices
    - controlar cardinalidade no serializer
    """

    IDEA_VIEW_OPENED = "idea_view_opened"
    IDEA_COPY_CLICKED = "idea_copy_clicked"
    IDEA_REGENERATE_CLICKED = "idea_regenerate_clicked"

    IMAGE_GENERATE_CLICKED = "image_generate_clicked"
    IMAGE_REGENERATE_CLICKED = "image_regenerate_clicked"
    IMAGE_DOWNLOAD_CLICKED = "image_download_clicked"
    IMAGE_DOWNLOAD_SUCCEEDED = "image_download_succeeded"
    IMAGE_DOWNLOAD_FAILED = "image_download_failed"

    POST_SAVE_CLICKED = "post_save_clicked"

    DECISION_MADE = "decision_made"

    @classmethod
    def allowed(cls) -> set[str]:
        return {
            cls.IDEA_VIEW_OPENED,
            cls.IDEA_COPY_CLICKED,
            cls.IDEA_REGENERATE_CLICKED,
            cls.IMAGE_GENERATE_CLICKED,
            cls.IMAGE_REGENERATE_CLICKED,
            cls.IMAGE_DOWNLOAD_CLICKED,
            cls.IMAGE_DOWNLOAD_SUCCEEDED,
            cls.IMAGE_DOWNLOAD_FAILED,
            cls.POST_SAVE_CLICKED,
            cls.DECISION_MADE,
        }


class AnalyticsResourceType:
    POST = "Post"
    POST_IDEA = "PostIdea"
    USER = "User"

    @classmethod
    def allowed(cls) -> set[str]:
        return {cls.POST, cls.POST_IDEA, cls.USER}

