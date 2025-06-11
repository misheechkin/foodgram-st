from django.db import models
from django.contrib.auth.models import AbstractUser


class Profile(AbstractUser):
    email = models.EmailField(
        unique=True,
        max_length=255
    )


    last_name = models.CharField(
        max_length=255,
        blank=True,
    )

    username = models.CharField(
        max_length=255,
        unique=True,
    )

    first_name = models.CharField(
        max_length=255,
        blank=True,
    )


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'first_name',
        'username',
        'password'
        'last_name',
    ]

    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='profiles/avatars/',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'профиль'
        verbose_name_plural = 'профили'

    def __str__(self):
        return self.username


class Follow(models.Model):

    author = models.ForeignKey(
        Profile,
        related_name='followers',
        on_delete=models.CASCADE,
        verbose_name='автор'
    )
    subscriber = models.ForeignKey(
        Profile,
        related_name='subscriptions',
        on_delete=models.CASCADE,
        verbose_name='подписчик'
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'subscriber'],
                name='unique_follow'
            )
        ]

    def __str__(self):
        return f'{self.subscriber} → {self.author}'
