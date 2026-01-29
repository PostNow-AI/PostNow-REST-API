"""
Instagram Notification Service
Creates and manages user notifications for Instagram integration events.
"""

from SocialMediaIntegration.models import InstagramNotification


class InstagramNotificationService:
    """
    Service for creating and managing Instagram-related notifications.
    """

    @staticmethod
    def create_notification(user, notification_type, message, action_url=None):
        """
        Create a new notification for a user.

        Args:
            user: Django User object
            notification_type: Type of notification (from NOTIFICATION_TYPE_CHOICES)
            message: Notification message
            action_url: Optional URL for user action

        Returns:
            InstagramNotification object
        """
        notification = InstagramNotification.objects.create(
            user=user,
            notification_type=notification_type,
            message=message,
            action_url=action_url
        )
        return notification

    @staticmethod
    def notify_first_connection(user, instagram_username):
        """Create notification for successful first connection"""
        message = (
            f"🎉 Instagram @{instagram_username} conectado com sucesso! "
            f"Agora você pode ver seus insights e melhorar seu conteúdo."
        )
        return InstagramNotificationService.create_notification(
            user=user,
            notification_type='first_connection',
            message=message,
            action_url='/dashboard/instagram'
        )

    @staticmethod
    def notify_token_expiring(user, instagram_username, days_left):
        """Create notification for token expiring soon"""
        message = (
            f"⚠️ A conexão com @{instagram_username} expira em {days_left} dias. "
            f"Reconecte para continuar recebendo insights."
        )
        return InstagramNotificationService.create_notification(
            user=user,
            notification_type='token_expiring',
            message=message,
            action_url='/settings/instagram'
        )

    @staticmethod
    def notify_sync_error(user, instagram_username, error_type='generic'):
        """Create notification for sync errors"""
        error_messages = {
            'rate_limit': (
                f"⏳ Muitas atualizações recentes para @{instagram_username}. "
                f"A próxima sincronização estará disponível em breve."
            ),
            'invalid_token': (
                f"🔒 A conexão com @{instagram_username} foi perdida. "
                f"Reconecte sua conta para continuar."
            ),
            'account_changed': (
                f"⚠️ Sua conta @{instagram_username} foi alterada para Personal. "
                f"Converta para Business/Creator para continuar usando insights."
            ),
            'generic': (
                f"❌ Erro ao sincronizar @{instagram_username}. "
                f"Tente novamente mais tarde ou reconecte sua conta."
            ),
        }

        message = error_messages.get(error_type, error_messages['generic'])

        return InstagramNotificationService.create_notification(
            user=user,
            notification_type='sync_error',
            message=message,
            action_url='/settings/instagram'
        )

    @staticmethod
    def notify_sync_success(user, instagram_username, new_followers=0):
        """Create notification for successful sync"""
        if new_followers > 0:
            message = (
                f"✅ Dados de @{instagram_username} atualizados! "
                f"Você ganhou {new_followers} novos seguidores esta semana. 🎉"
            )
        else:
            message = (
                f"✅ Dados de @{instagram_username} atualizados com sucesso!"
            )

        return InstagramNotificationService.create_notification(
            user=user,
            notification_type='sync_success',
            message=message,
            action_url='/dashboard/instagram'
        )

    @staticmethod
    def notify_connection_lost(user, instagram_username):
        """Create notification when connection is lost"""
        message = (
            f"🔌 Conexão com @{instagram_username} foi perdida. "
            f"Reconecte para continuar visualizando seus insights."
        )
        return InstagramNotificationService.create_notification(
            user=user,
            notification_type='connection_lost',
            message=message,
            action_url='/settings/instagram'
        )

    @staticmethod
    def notify_achievement_unlocked(user):
        """Create notification for achievement unlock"""
        message = (
            "🏆 Conquista Desbloqueada: Analista de Dados! "
            "Você ganhou 50 créditos grátis por conectar seu Instagram."
        )
        return InstagramNotificationService.create_notification(
            user=user,
            notification_type='achievement_unlocked',
            message=message,
            action_url='/profile/achievements'
        )

    @staticmethod
    def get_unread_notifications(user):
        """Get all unread notifications for a user"""
        return InstagramNotification.objects.filter(
            user=user,
            is_read=False
        ).order_by('-created_at')

    @staticmethod
    def mark_all_as_read(user):
        """Mark all notifications as read for a user"""
        notifications = InstagramNotification.objects.filter(
            user=user,
            is_read=False
        )

        count = notifications.count()
        for notification in notifications:
            notification.mark_as_read()

        return count
