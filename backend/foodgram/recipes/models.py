from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from rest_framework.validators import ValidationError

User = get_user_model()


def validate_positive(value):
    if not value or value < 1:
        raise ValidationError(
            'Недопустимое значение!'
        )


class Ingredient(models.Model):

    name = models.CharField(('Название'), max_length=256)
    measurement_unit = models.CharField(
        ('Единица измерения'),
        max_length=64
    )

    class Meta:
        ordering = ['name']
        verbose_name = ('Ингредиент')
        verbose_name_plural = ('Ингредиенты')

    def __str__(self):
        return f"{self.name} - {self.measurement_unit}"


class Recipe(models.Model):

    name = models.CharField(('Название'), max_length=256)
    text = models.TextField(('Описание'))
    cooking_time = models.PositiveSmallIntegerField(
        ('Время приготовления'),
        validators=[
            validate_positive,
            MinValueValidator(1, message=('Значение должно быть больше нуля!'))
        ]
    )
    image = models.ImageField(
        ('Фото'),
        upload_to='recipes/images'
    )
    author = models.ForeignKey(
        User,
        verbose_name=('Автор'),
        related_name='recipes',
        on_delete=models.CASCADE
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        related_name='recipes',
        verbose_name=('Ингредиенты'),
        through_fields=('recipe', 'ingredient')
    )
    created_at = models.DateTimeField(
        ('Добавлено'),
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = ('Рецепт')
        verbose_name_plural = ('Рецепты')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('recipes-detail', kwargs={'pk': self.pk})


class IngredientRecipe(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_ingredients',
        verbose_name=('Рецепт'),
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name=('Ингредиент'),
        on_delete=models.CASCADE
    )
    amount = models.PositiveIntegerField(
        ('Количество'),
        validators=[
            validate_positive,
            MinValueValidator(1, message=('Значение должно быть больше нуля!'))
        ]
    )

    class Meta:
        verbose_name = ('Ингредиент в рецепте')
        verbose_name_plural = ('Ингредиенты в рецепте')
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.ingredient} - {self.recipe}'

class CartItem(models.Model):
    """Модель для элементов корзины покупок."""
    user = models.ForeignKey(
        User,
        related_name='cart',
        verbose_name=('Пользователь'),
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='shopping_carts',
        verbose_name=('Рецепт'),
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = ('элемент корзины')
        verbose_name_plural = ('Элементы корзины')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_cart'
            )
        ]

    def __str__(self):
        return f"{self.recipe} добавлен в корзину {self.user}"


class Favorites(models.Model):
    """Модель списка избранных рецептов."""
    user = models.ForeignKey(
        User,
        related_name='favs',
        verbose_name=('Пользователь'),
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='user_favs',
        verbose_name=('Рецепт'),
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = ('избранное')
        verbose_name_plural = ('Избранное')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_user_fav'
            )
        ]

    def __str__(self):
        return f"{self.recipe.title} — корзина {self.owner.username}"
