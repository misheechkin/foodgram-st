from base64 import b64decode
import uuid
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from rest_framework import serializers

from .models import CookingRecipe, ProductComponent, RecipeComponent, FavoriteRecipe, ShoppingCart
from users.serializers import UserSerializer


class ProductSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProductComponent
        fields = '__all__'


class ComponentInputSerializer(serializers.Serializer):
    
    id = serializers.PrimaryKeyRelatedField(queryset=ProductComponent.objects.all())
    quantity = serializers.IntegerField(
        min_value=1,
        error_messages={'min_value': 'Количество должно быть не менее 1!'}
    )


class ComponentOutputSerializer(serializers.ModelSerializer):
    
    id = serializers.IntegerField(source='component.id')
    title = serializers.CharField(source='component.title')
    unit_type = serializers.CharField(source='component.unit_type')
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeComponent
        fields = ('id', 'title', 'unit_type', 'quantity')


class Base64ImageField(serializers.ImageField):
    
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format_part, image_data = data.split(';base64,')
            extension = format_part.split('/')[-1]
            file_name = f"recipe_{uuid.uuid4().hex[:8]}.{extension}"
            data = ContentFile(b64decode(image_data), name=file_name)
        return super().to_internal_value(data)


class CookingRecipeSerializer(serializers.ModelSerializer):
    
    creator = UserSerializer(read_only=True)
    picture = Base64ImageField(required=True)
    components = serializers.ListField(
        child=ComponentInputSerializer(),
        write_only=True
    )
    components_info = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cook_duration = serializers.IntegerField(
        min_value=1,
        error_messages={'min_value': 'Время приготовления должно быть больше 0!'}
    )

    class Meta:
        model = CookingRecipe
        fields = (
            'id', 'creator', 'title', 'description', 'picture', 'cook_duration',
            'components', 'components_info', 'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = ('creator', 'components_info', 'is_favorited', 'is_in_shopping_cart')

    def get_components_info(self, obj):
        queryset = obj.recipe_components.select_related('component')
        return ComponentOutputSerializer(queryset, many=True).data

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if not user or not user.is_authenticated:
            return False
        return FavoriteRecipe.objects.filter(owner=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if not user or not user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(customer=user, recipe=obj).exists()

    def validate_components(self, components_list):
        if not isinstance(components_list, list) or not components_list:
            raise serializers.ValidationError('Список ингредиентов не может быть пустым!')
        
        component_ids = [
            item['id'].id if hasattr(item['id'], 'id') else item['id'] 
            for item in components_list
        ]
        
        if len(component_ids) != len(set(component_ids)):
            raise serializers.ValidationError('Ингредиенты не должны повторяться!')
        
        return components_list

    def create(self, validated_data):
        components = validated_data.pop('components')
        recipe = CookingRecipe.objects.create(**validated_data)
        self._create_recipe_components(recipe, components)
        return recipe

    def update(self, instance, validated_data):
        components = validated_data.pop('components', None)
        
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        
        if components is not None:
            instance.recipe_components.all().delete()
            self._create_recipe_components(instance, components)
        
        return instance

    def _create_recipe_components(self, recipe, components):
        component_objects = []
        existing_components = ProductComponent.objects.in_bulk(
            [item['id'] for item in components]
        )
        
        if len(existing_components) != len(components):
            raise serializers.ValidationError('Некоторые ингредиенты не найдены!')
        
        for component_data in components:
            component = existing_components[component_data['id']]
            quantity = component_data['quantity']
            
            if quantity < 1:
                raise serializers.ValidationError('Количество ингредиента должно быть больше 0!')
            
            component_objects.append(RecipeComponent(
                recipe=recipe,
                component=component,
                quantity=quantity
            ))
        
        RecipeComponent.objects.bulk_create(component_objects)


class CookingRecipeShortSerializer(serializers.ModelSerializer):
    
    picture = Base64ImageField(required=True)

    class Meta:
        model = CookingRecipe
        fields = ('id', 'title', 'picture', 'cook_duration')


class UserSubscriptionSerializer(UserSerializer):
    
    authored_recipes = serializers.SerializerMethodField()
    authored_recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = [*UserSerializer.Meta.fields, 'authored_recipes', 'authored_recipes_count']

    def get_authored_recipes(self, user):
        recipes_queryset = user.authored_recipes.all()
        recipes_limit = self.context['request'].query_params.get('recipes_limit')
        
        if recipes_limit:
            paginator = Paginator(recipes_queryset, int(recipes_limit))
            recipes_queryset = paginator.page(1).object_list
        
        return CookingRecipeShortSerializer(
            recipes_queryset, 
            many=True, 
            context=self.context
        ).data

    def get_authored_recipes_count(self, user):
        return user.authored_recipes.count()
