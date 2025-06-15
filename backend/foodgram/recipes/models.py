from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework.validators import ValidationError


class User(AbstractUser):
    
    email = models.EmailField(_('Электронная почта'), unique=True, max_length=254)
    username = models.CharField(
        _('Псевдоним пользователя'),
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message=_('Недопустимые символы в псевдониме пользователя!')
            )
        ]
    )
    first_name = models.CharField(_('Имя'), max_length=150)
    last_name = models.CharField(_('Фамилия'), max_length=150)
    avatar = models.ImageField(
        _('Аватар пользователя'),
        upload_to='users/avatars',
        null=True,
        blank=True
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta(AbstractUser.Meta):
        ordering = ('username',)
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')


class UserSubscription(models.Model):
    
    subscriber = models.ForeignKey(
        'User',
        verbose_name=_('Подписчик'),
        related_name='following',
        on_delete=models.CASCADE
    )
    target_user = models.ForeignKey(
        'User',
        verbose_name=_('На кого подписан'),
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
        verbose_name = _('Подписка')
        verbose_name_plural = _('Подписки')

    def __str__(self):
        return _('%(subscriber)s подписан на %(target_user)s') % {
            'subscriber': self.subscriber,
            'target_user': self.target_user
        }


def check_positive_value(val):
    if not val or val < 1:
        raise ValidationError(_('Значение должно быть положительным!'))


class ProductComponent(models.Model):
    
    title = models.CharField(_('Наименование'), max_length=256)
    unit_type = models.CharField(_('Единица измерения'), max_length=64)

    class Meta:
        ordering = ('title',)
        verbose_name = _('Продукт')
        verbose_name_plural = _('Продукты')

    def __str__(self):
        return f"{self.title} ({self.unit_type})"


# Базовый класс для Избранного и Корзины
class BaseUserRecipeRelation(models.Model):
    
    user = models.ForeignKey(
        'User',
        verbose_name=_('Пользователь'),
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        'CookingRecipe',
        verbose_name=_('Рецепт'),
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(class)s_unique_user_recipe'
            )
        ]

    def __str__(self):
        return _('%(recipe)s - %(user)s') % {
            'recipe': self.recipe,
            'user': self.user
        }


class CookingRecipe(models.Model):
    
    title = models.CharField(_('Название рецепта'), max_length=256)
    description = models.TextField(_('Описание приготовления'))
    cook_duration = models.PositiveSmallIntegerField(
        _('Время приготовления (мин)'),
        validators=[
            check_positive_value,
            MinValueValidator(1, message=_('Время должно быть больше 0 минут!'))
        ]
    )
    picture = models.ImageField(_('Изображение блюда'), upload_to='recipes/images')
    creator = models.ForeignKey(
        'User',
        verbose_name=_('Автор рецепта'),
        related_name='authored_recipes',
        on_delete=models.CASCADE
    )
    components = models.ManyToManyField(
        ProductComponent,
        through='RecipeComponent',
        related_name='used_in_recipes',
        verbose_name=_('Список продуктов'),
        through_fields=('recipe', 'component')
    )
    date_created = models.DateTimeField(_('Дата создания'), auto_now_add=True)

    class Meta:
        ordering = ('-date_created',)
        verbose_name = _('Рецепт')
        verbose_name_plural = _('Рецепты')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('recipes-detail', kwargs={'pk': self.pk})


class RecipeComponent(models.Model):
    
    recipe = models.ForeignKey(
        CookingRecipe,
        related_name='recipe_components',
        verbose_name=_('Рецепт'),
        on_delete=models.CASCADE
    )
    component = models.ForeignKey(
        ProductComponent,
        verbose_name=_('Продукт'),
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(
        _('Количество'),
        validators=[
            check_positive_value,
            MinValueValidator(1, message=_('Количество должно быть больше 0!'))
        ]
    )

    class Meta:
        ordering = ('recipe', 'component')
        verbose_name = _('Продукт в рецепте')
        verbose_name_plural = _('Продукты в рецептах')
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'component'],
                name='unique_recipe_component'
            )
        ]

    def __str__(self):
        return _('%(component)s для %(recipe)s') % {
            'component': self.component,
            'recipe': self.recipe
        }

class ShoppingCart(BaseUserRecipeRelation):
    
    user = models.ForeignKey(
        'User',
        verbose_name=_('Покупатель'),
        related_name='shopping_items',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        CookingRecipe,
        verbose_name=_('Рецепт'),
        related_name='in_shopping_carts',
        on_delete=models.CASCADE
    )
    
    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = _('Элемент корзины')
        verbose_name_plural = _('Корзина покупок')


class FavoriteRecipe(BaseUserRecipeRelation):
    
    user = models.ForeignKey(
        'User',
        verbose_name=_('Пользователь'),
        related_name='favorite_recipes',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        CookingRecipe,
        verbose_name=_('Рецепт'),
        related_name='favorites',
        on_delete=models.CASCADE
    )
    
    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = _('Избранный рецепт')
        verbose_name_plural = _('Избранные рецепты')
