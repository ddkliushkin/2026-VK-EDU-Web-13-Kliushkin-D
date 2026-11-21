import os
import uuid
from django.db import models
from django.contrib.auth.models import User


def avatar_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f'avatars/{uuid.uuid4().hex}{ext}'


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь',
    )
    nickname = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Никнейм',
    )
    avatar = models.ImageField(
        upload_to=avatar_upload_path,
        blank=True,
        null=True,
        verbose_name='Аватар',
    )

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return self.nickname or self.user.username

    @property
    def display_name(self):
        return self.nickname or self.user.username