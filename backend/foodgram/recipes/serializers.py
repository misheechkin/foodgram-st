from base64 import b64decode
from io import StringIO
from django.contrib.auth import get_user
from django.core.files.base import ContentFile
from rest_framework import serializers,status
from django.http import FileResponse
from rest_framework.response import Response
from .models import Recipe, Ingredient, IngredientRecipe, ShoppingCart


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            fmt, img_str = data.split(';base64,')
            ext = fmt.split('/')[-1]
            data = ContentFile(b64decode(img_str), name=f'temp.{ext}')
        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', queryset=Ingredient.objects.all()
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )
    amount = serializers.FloatField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientRecipeSerializer(
        source='ingredientrecipe_set', many=True
    )
    image = Base64ImageField(required=False, allow_null=True)
    image_url = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'cooking_time', 'image', 'image_url',
            'author', 'ingredients', 'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = ('author',)

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None

    def get_is_favorited(self, obj):
        return False

    def get_is_in_shopping_cart(self, obj):
        return False

    def _create_or_update_ingredients(self, recipe, ingredients_data):
        IngredientRecipe.objects.filter(recipe=recipe).delete()
        for item in ingredients_data:
            ingredient = item['ingredient']
            amount = item['amount']
            IngredientRecipe.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount
            )

    def create(self, validated_data):
        ing_data = validated_data.pop('ingredientrecipe_set', [])
        recipe = Recipe.objects.create(**validated_data)
        for item in ing_data:
            ing = item['ingredient']
            IngredientRecipe.objects.create(
                recipe=recipe,
                ingredient=ing,
                amount=item['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        ing_data = validated_data.pop('ingredientrecipe_set', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if ing_data is not None:
            self._create_or_update_ingredients(instance, ing_data)
        return instance
    

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def post_delete_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = get_user(request=request)

        if request.method == 'POST':
            note, created = ShoppingCart.objects.get_or_create(
                user=user, recipe=recipe)
            if not created:
                return Response(detail='Рецепт уже в списке покупок!',
                                status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            count, var = ShoppingCart.objects.filter(
                user=user, recipe=recipe).delete()
            if count == 0:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='download-shopping-cart')
    def download_cart(self, request):
        user = get_user(request=request)

        ingredients = {}

        pk_in_cart = ShoppingCart.objects.filter(user=user)
        for recipe_pk in pk_in_cart:
            in_recipe = Recipe.objects.get(pk=recipe_pk).ingredients
            for ingr in in_recipe:
                product = Ingredient.objects.get(pk=ingr.pk)
                if product in ingredients.keys:
                    ingredients[product] += ingr.amount
                else:
                    ingredients[product] = ingr.amount

        if len(ingredients) == 0:
            return Response(detail='Список покупок пуст!',
                            status=status.HTTP_200_OK)

        file = StringIO()
        for ingredient, amount in ingredients:
            s = f'{ingredient.name} - {amount} {ingredient.measurement_unit}\n'
            file.write(s)

        return FileResponse(file, as_attachment=True,
                            filename='shoppingcart.txt')
