from base64 import b64decode
import uuid
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from rest_framework import serializers

from .models import Recipe, Ingredient, IngredientRecipe, Favorites, CartItem
from users.serializers import UserProfileSerializer


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeInputSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=1,
        error_messages={'min_value': 'Количество должно быть ≥ 1!'}
    )


class IngredientRecipeOutputSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit')
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class Base64ImageField(serializers.ImageField):
    """Поле для представления картинки в формате base64."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            filename = f"pic_{uuid.uuid4().hex[:8]}.{ext}"
            data = ContentFile(b64decode(imgstr), name=filename)
        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True)
    image = Base64ImageField(required=True)
    ingredients = serializers.ListField(
        child=IngredientRecipeInputSerializer(),
        write_only=True
    )
    ingredients_info = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField(
        min_value=1,
        error_messages={'min_value': 'Время должно быть > 0!'}
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'text', 'image', 'cooking_time',
            'ingredients', 'ingredients_info', 'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = ('author', 'ingredients_info', 'is_favorited', 'is_in_shopping_cart')

    def get_ingredients_info(self, recipe):
        qs = recipe.recipe_ingredients.select_related('ingredient')
        return IngredientRecipeOutputSerializer(qs, many=True).data

    def get_is_favorited(self, recipe):
        user = self.context.get('request').user
        if not user or not user.is_authenticated:
            return False
        return Favorites.objects.filter(user=user, recipe=recipe).exists()

    def get_is_in_shopping_cart(self, recipe):
        user = self.context.get('request').user
        if not user or not user.is_authenticated:
            return False
        return CartItem.objects.filter(user=user, recipe=recipe).exists()

    def validate_ingredients(self, items):
        if not isinstance(items, list) or not items:
            raise serializers.ValidationError('Нужно передать непустой список ингредиентов!')
        ids = [it['id'].id if hasattr(it['id'], 'id') else it['id'] for it in items]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError('Ингредиенты не могут дублироваться!')
        return items

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self._save_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if ingredients is not None:
            instance.recipe_ingredients.all().delete()
            self._save_ingredients(instance, ingredients)
        return instance

    def _save_ingredients(self, recipe, ingredients):
        objs = []
        existing = Ingredient.objects.in_bulk([item['id'] for item in ingredients])
        if len(existing) != len(ingredients):
            raise serializers.ValidationError('Один из ингредиентов не найден!')
        for entry in ingredients:
            ing = existing[entry['id']]
            amount = entry['amount']
            if amount < 1:
                raise serializers.ValidationError('Количество ингредиента должно быть > 0!')
            objs.append(IngredientRecipe(
                recipe=recipe,
                ingredient=ing,
                amount=amount
            ))
        IngredientRecipe.objects.bulk_create(objs)


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(UserProfileSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserProfileSerializer.Meta):
        fields = [*UserProfileSerializer.Meta.fields, 'recipes', 'recipes_count']

    def get_recipes(self, user):
        qs = user.recipes.all()
        limit = self.context['request'].query_params.get('recipes_limit')
        if limit:
            paginator = Paginator(qs, int(limit))
            qs = paginator.page(1).object_list
        return ShortRecipeSerializer(qs, many=True, context=self.context).data

    def get_recipes_count(self, user):
        return user.recipes.count()
