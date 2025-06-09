from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

User = get_user_model()

class Ingredient(models.Model):
    """Ингредиент для рецепта."""

    name = models.CharField(('Название'), max_length=256)
    measurement_unit = models.CharField(
        ('Единица измерения'),
        max_length=64
    )

    class Meta:
        verbose_name = ('Ингредиент')
        verbose_name_plural = ('Ингредиенты')

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Рецепт блюда."""

    name = models.CharField(('Название'), max_length=256)
    text = models.TextField(('Описание'))
    cooking_time = models.PositiveSmallIntegerField(
        ('Время приготовления (мин)')
    )
    image = models.ImageField(
        ('Фото'),
        upload_to='recipes/images/',
        blank=True,
        null=True
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
        verbose_name=('Ингредиенты')
    )

    class Meta:
        verbose_name = ('Рецепт')
        verbose_name_plural = ('Рецепты')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('recipe-detail', kwargs={'pk': self.pk})


class IngredientRecipe(models.Model):
    """Связь ингредиента и рецепта с количеством."""

    recipe = models.ForeignKey(
        Recipe,
        verbose_name=('Рецепт'),
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name=('Ингредиент'),
        on_delete=models.CASCADE
    )
    amount = models.FloatField(('Количество'))

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
