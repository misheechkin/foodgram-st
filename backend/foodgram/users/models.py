from re import match
from django.db import models
from django.contrib.auth.models import AbstractUser
from rest_framework.validators import ValidationError


def check_username_format(username_value):
    if not match(r'^[\w.@+-]+\Z', username_value):
        raise ValidationError('Недопустимые символы в имени пользователя!')


class User(AbstractUser):
    
    email = models.EmailField('Электронная почта', unique=True, max_length=254)
    username = models.CharField(
        'Имя пользователя',
        max_length=150,
        unique=True,
        validators=[check_username_format]
    )
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    avatar = models.ImageField(
        'Аватар пользователя',
        upload_to='users/avatars',
        null=True,
        blank=True
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta(AbstractUser.Meta):
        db_table = 'auth_user'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class UserSubscription(models.Model):
    
    subscriber = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        related_name='following',
        on_delete=models.CASCADE
    )
    target_user = models.ForeignKey(
        User,
        verbose_name='На кого подписан',
        related_name='followers',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'target_user'],
                name='unique_user_subscription'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.subscriber} подписан на {self.target_user}'