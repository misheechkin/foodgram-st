from re import match
from django.db import models
from django.contrib.auth.models import AbstractUser
from rest_framework.validators import ValidationError


def validate_username(value):
    if not match(r'^[\w.@+-]+\Z', value):
        raise ValidationError(
            'Недопустимые символы: ^[\\w.@+-]+\\z'
        )


class UserProfile(AbstractUser):

    email = models.EmailField(
        unique=True,
        max_length=254
    )

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[validate_username]
    )

    first_name = models.CharField(
        max_length=150,
        blank=False,
        null=False
    )

    last_name = models.CharField(
        max_length=150,
        blank=False,
        null=False
    )

    avatar = models.ImageField(
        'Аватар',
        upload_to='users/images',
        null=True,
        default=None
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
        'password'
    ]

    class Meta(AbstractUser.Meta):
        db_table = 'auth_user'
        verbose_name = 'профиль пользователя'
        verbose_name_plural = 'Профили пользователей'


class Subscription(models.Model):

    user = models.ForeignKey(
        UserProfile,
        verbose_name='Пользователь',
        related_name='subscriber',
        on_delete=models.CASCADE
    )
    follows = models.ForeignKey(
        UserProfile,
        verbose_name='Подписка',
        related_name='subbed_to',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'follows'],
                                    name="unique_subs")
        ]
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'