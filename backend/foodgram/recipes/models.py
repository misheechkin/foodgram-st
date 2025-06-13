from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from rest_framework.validators import ValidationError

UserModel = get_user_model()


def check_positive_value(val):
    if not val or val < 1:
        raise ValidationError('Значение должно быть положительным!')


class ProductComponent(models.Model):
    
    title = models.CharField('Наименование', max_length=256)
    unit_type = models.CharField('Единица измерения', max_length=64)

    class Meta:
        ordering = ['title']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f"{self.title} ({self.unit_type})"


class CookingRecipe(models.Model):
    
    title = models.CharField('Название рецепта', max_length=256)
    description = models.TextField('Описание приготовления')
    cook_duration = models.PositiveSmallIntegerField(
        'Время приготовления (мин)',
        validators=[
            check_positive_value,
            MinValueValidator(1, message='Время должно быть больше 0 минут!')
        ]
    )
    picture = models.ImageField('Изображение блюда', upload_to='recipes/images')
    creator = models.ForeignKey(
        UserModel,
        verbose_name='Автор рецепта',
        related_name='authored_recipes',
        on_delete=models.CASCADE
    )
    components = models.ManyToManyField(
        ProductComponent,
        through='RecipeComponent',
        related_name='used_in_recipes',
        verbose_name='Список ингредиентов',
        through_fields=('recipe', 'component')
    )
    date_created = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        ordering = ['-date_created']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('recipes-detail', kwargs={'pk': self.pk})


class RecipeComponent(models.Model):
    
    recipe = models.ForeignKey(
        CookingRecipe,
        related_name='recipe_components',
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )
    component = models.ForeignKey(
        ProductComponent,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(
        'Количество',
        validators=[
            check_positive_value,
            MinValueValidator(1, message='Количество должно быть больше 0!')
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'component'],
                name='unique_recipe_component'
            )
        ]

    def __str__(self):
        return f'{self.component} для {self.recipe}'

class ShoppingCart(models.Model):
    
    customer = models.ForeignKey(
        UserModel,
        related_name='shopping_items',
        verbose_name='Покупатель',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        CookingRecipe,
        related_name='in_shopping_carts',
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Корзина покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['customer', 'recipe'],
                name='unique_customer_recipe_cart'
            )
        ]

    def __str__(self):
        return f"{self.recipe} в корзине {self.customer}"


class FavoriteRecipe(models.Model):
    
    owner = models.ForeignKey(
        UserModel,
        related_name='favorite_recipes',
        verbose_name='Пользователь',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        CookingRecipe,
        related_name='favorited_by',
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'recipe'],
                name='unique_favorite_recipe'
            )
        ]

    def __str__(self):
        return f"{self.recipe} в избранном у {self.owner}"
