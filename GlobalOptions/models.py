from django.contrib.auth.models import User
from django.db import models


class CustomProfession(models.Model):
    """
    Modelo para profissões customizadas criadas pelos usuários.
    Todas as profissões são compartilhadas globalmente.
    """

    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Nome da Profissão",
        help_text="Nome da profissão customizada"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Criado por",
        help_text="Usuário que criou esta profissão"
    )

    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Contador de Uso",
        help_text="Quantas vezes esta profissão foi utilizada"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Se esta profissão está ativa para uso"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profissão Customizada"
        verbose_name_plural = "Profissões Customizadas"
        ordering = ['-usage_count', 'name']

    def __str__(self):
        return self.name


class CustomSpecialization(models.Model):
    """
    Modelo para especializações customizadas criadas pelos usuários.
    Cada especialização é obrigatoriamente relacionada a uma profissão.
    """

    name = models.CharField(
        max_length=200,
        verbose_name="Nome da Especialização",
        help_text="Nome da especialização customizada"
    )

    profession = models.ForeignKey(
        CustomProfession,
        on_delete=models.CASCADE,
        related_name='specializations',
        verbose_name="Profissão",
        help_text="Profissão à qual esta especialização pertence"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Criado por",
        help_text="Usuário que criou esta especialização"
    )

    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Contador de Uso",
        help_text="Quantas vezes esta especialização foi utilizada"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Se esta especialização está ativa para uso"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Especialização Customizada"
        verbose_name_plural = "Especializações Customizadas"
        ordering = ['-usage_count', 'name']
        unique_together = ['name', 'profession']  # Nome único por profissão

    def __str__(self):
        return f"{self.name} ({self.profession.name})"


class CustomSpecializationForProfession(models.Model):
    """
    Modelo intermediário para permitir especializações customizadas para qualquer profissão.
    """

    name = models.CharField(
        max_length=200,
        verbose_name="Nome da Especialização",
        help_text="Nome da especialização customizada"
    )

    profession_name = models.CharField(
        max_length=200,
        verbose_name="Nome da Profissão",
        help_text="Nome da profissão à qual esta especialização pertence"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Criado por",
        help_text="Usuário que criou esta especialização"
    )

    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Contador de Uso",
        help_text="Quantas vezes esta especialização foi utilizada"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Se esta especialização está ativa para uso"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Especialização Customizada para Profissão"
        verbose_name_plural = "Especializações Customizadas para Profissões"
        ordering = ['-usage_count', 'name']
        # Nome único por profissão
        unique_together = ['name', 'profession_name']

    def __str__(self):
        return f"{self.name} ({self.profession_name})"


class CustomFont(models.Model):
    """
    Modelo para fontes customizadas criadas pelos usuários.
    Todas as fontes são compartilhadas globalmente.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nome da Fonte",
        help_text="Nome da fonte customizada"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Criado por",
        help_text="Usuário que criou esta fonte"
    )

    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Contador de Uso",
        help_text="Quantas vezes esta fonte foi utilizada"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Se esta fonte está ativa para uso"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fonte Customizada"
        verbose_name_plural = "Fontes Customizadas"
        ordering = ['-usage_count', 'name']

    def __str__(self):
        return self.name


class PredefinedProfession(models.Model):
    """
    Modelo para profissões predefinidas do sistema.
    Estas são as profissões padrão que já existem.
    """

    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Nome da Profissão",
        help_text="Nome da profissão predefinida"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Se esta profissão está ativa para uso"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profissão Predefinida"
        verbose_name_plural = "Profissões Predefinidas"
        ordering = ['name']

    def __str__(self):
        return self.name


class PredefinedSpecialization(models.Model):
    """
    Modelo para especializações predefinidas do sistema.
    Cada especialização é obrigatoriamente relacionada a uma profissão.
    """

    name = models.CharField(
        max_length=200,
        verbose_name="Nome da Especialização",
        help_text="Nome da especialização predefinida"
    )

    profession = models.ForeignKey(
        PredefinedProfession,
        on_delete=models.CASCADE,
        related_name='specializations',
        verbose_name="Profissão",
        help_text="Profissão à qual esta especialização pertence"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Se esta especialização está ativa para uso"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Especialização Predefinida"
        verbose_name_plural = "Especializações Predefinidas"
        ordering = ['name']
        unique_together = ['name', 'profession']  # Nome único por profissão

    def __str__(self):
        return f"{self.name} ({self.profession.name})"


class PredefinedFont(models.Model):
    """
    Modelo para fontes predefinidas do sistema.
    Estas são as fontes padrão que já existem.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nome da Fonte",
        help_text="Nome da fonte predefinida"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Se esta fonte está ativa para uso"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fonte Predefinida"
        verbose_name_plural = "Fontes Predefinidas"
        ordering = ['name']

    def __str__(self):
        return self.name
