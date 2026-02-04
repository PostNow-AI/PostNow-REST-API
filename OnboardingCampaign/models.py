from django.contrib.auth.models import User
from django.db import models


class OnboardingEmail(models.Model):
    """
    Tracks sent onboarding emails for users who haven't completed onboarding.
    Part of a 3-email campaign (Day 1, 3, 7 after subscription activation).
    """

    # Email numbers in the campaign sequence
    EMAIL_1 = 1  # Day 1: "Deu tudo certo com o seu cadastro?"
    EMAIL_2 = 2  # Day 3: "Um post pronto te esperando..."
    EMAIL_3 = 3  # Day 7: "Não quero ser o \"chato\" do e-mail"

    EMAIL_NUMBER_CHOICES = [
        (EMAIL_1, 'Email 1 - Dia 1'),
        (EMAIL_2, 'Email 2 - Dia 3'),
        (EMAIL_3, 'Email 3 - Dia 7'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='onboarding_emails',
        verbose_name='Usuário'
    )

    email_number = models.IntegerField(
        choices=EMAIL_NUMBER_CHOICES,
        verbose_name='Número do Email'
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Enviado Em',
        help_text='Data e hora em que o email foi enviado'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Email de Onboarding'
        verbose_name_plural = 'Emails de Onboarding'
        ordering = ['-sent_at']
        unique_together = ['user', 'email_number']
        indexes = [
            models.Index(fields=['user', 'email_number']),
            models.Index(fields=['sent_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - Email {self.email_number} - Enviado"

    @property
    def template_name(self):
        """Get the email template name for this email number."""
        return f'onboarding/email_{self.email_number}.html'


class ReactivationEmail(models.Model):
    """
    Tracks sent reactivation emails for users who had subscriptions until Dec 25, 2025.
    Part of a 3-email campaign (Day 1, 3, 7 after campaign start).
    """

    # Email numbers in the campaign sequence
    EMAIL_1 = 1  # Day 1: "Apenas um obrigado (e algumas novidades por aqui)"
    EMAIL_2 = 2  # Day 3: "O Plano Legado: um presente para quem começou com a gente"
    EMAIL_3 = 3  # Day 7: "O Plano Legado: um presente para quem começou com a gente"

    EMAIL_NUMBER_CHOICES = [
        (EMAIL_1, 'Email 1 - Dia 1'),
        (EMAIL_2, 'Email 2 - Dia 3'),
        (EMAIL_3, 'Email 3 - Dia 7'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reactivation_emails',
        verbose_name='Usuário'
    )

    email_number = models.IntegerField(
        choices=EMAIL_NUMBER_CHOICES,
        verbose_name='Número do Email'
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Enviado Em',
        help_text='Data e hora em que o email foi enviado'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Email de Reativação'
        verbose_name_plural = 'Emails de Reativação'
        ordering = ['-sent_at']
        unique_together = ['user', 'email_number']
        indexes = [
            models.Index(fields=['user', 'email_number']),
            models.Index(fields=['sent_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - Reativação Email {self.email_number}"

    @property
    def template_name(self):
        """Get the email template name for this email number."""
        return f'reactivation/email_{self.email_number}.html'
