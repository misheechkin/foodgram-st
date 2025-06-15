from io import BytesIO
from datetime import datetime
from django.db.models import Sum
from django.http import FileResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import filters, viewsets, permissions, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet

from recipes.models import CookingRecipe, ProductComponent, ShoppingCart, RecipeComponent, FavoriteRecipe
from recipes.models import UserSubscription, User
from .serializers import (
    ProductSerializer, CookingRecipeSerializer, CookingRecipeShortSerializer, 
    UserSubscriptionSerializer, UserSerializer
)
from .permissions import CreatorOrReadOnly
from .filters import CookingRecipeFilter

UserModel = get_user_model()


class ProductComponentViewSet(viewsets.ReadOnlyModelViewSet):
    
    queryset = ProductComponent.objects.all()
    serializer_class = ProductSerializer
    pagination_class = None
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('title',)
    search_fields = ('^title',)

    def get_queryset(self):
        search_term = self.request.query_params.get('title')
        if search_term:
            return self.queryset.filter(title__istartswith=search_term)
        return self.queryset


class CookingRecipeViewSet(viewsets.ModelViewSet):
    
    serializer_class = CookingRecipeSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (CreatorOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('title',)
    filterset_class = CookingRecipeFilter

    def get_queryset(self):
        return (
            CookingRecipe.objects
            .select_related('creator')
            .prefetch_related('recipe_components__component', 'favorites', 'in_shopping_carts')
        )

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def _handle_recipe_relation(self, request, pk, model_class, error_messages):
        """Общий метод для управления избранным и корзиной"""
        recipe = get_object_or_404(CookingRecipe, pk=pk)
        user = request.user
        
        if request.method == 'POST':
            _, created = model_class.objects.get_or_create(user=user, recipe=recipe)
            if not created:
                return Response(
                    {'detail': error_messages['already_exists'].format(recipe=recipe.title)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = CookingRecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        relation = get_object_or_404(model_class, user=user, recipe=recipe)
        relation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, 
        methods=['post', 'delete'], 
        url_path='shopping-cart',
        permission_classes=[permissions.IsAuthenticated]
    )
    def handle_shopping_cart(self, request, pk=None):
        return self._handle_recipe_relation(
            request, pk, ShoppingCart,
            {'already_exists': 'Рецепт "{recipe}" уже в корзине'}
        )

    @action(
        detail=False, 
        methods=['get'], 
        url_path='download-shopping-list',
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_list(self, request):
        user = request.user
        shopping_list = (
            RecipeComponent.objects
            .filter(recipe__in_shopping_carts__user=user)
            .values('component__title', 'component__unit_type')
            .annotate(total_quantity=Sum('quantity'))
            .order_by('component__title')
        )
        
        recipes_in_cart = (
            CookingRecipe.objects
            .filter(in_shopping_carts__user=user)
            .select_related('creator')
            .values('title', 'creator__username', 'creator__first_name', 'creator__last_name')
        )
        
        content = '\n'.join([
            f'Список покупок на {datetime.now().strftime("%d.%m.%Y")}',
            '',
            'ПРОДУКТЫ:',
            *[
                f'{index}. {item["component__title"].capitalize()} - '
                f'{item["total_quantity"]} {item["component__unit_type"]}'
                for index, item in enumerate(shopping_list, 1)
            ],
            '',
            'РЕЦЕПТЫ:',
            *[
                f'• {recipe["title"]} (автор: '
                f'{recipe["creator__first_name"]} {recipe["creator__last_name"]} '
                f'@{recipe["creator__username"]})'
                for recipe in recipes_in_cart
            ],
        ])
        
        file_buffer = BytesIO()
        file_buffer.write(content.encode('utf-8'))
        file_buffer.seek(0)
        
        return FileResponse(
            file_buffer, 
            as_attachment=True, 
            filename='shopping_list.txt', 
            content_type='text/plain'
        )

    @action(
        detail=True, 
        methods=['post', 'delete'], 
        url_path='favorite',
        permission_classes=[permissions.IsAuthenticated]
    )
    def handle_favorites(self, request, pk=None):
        return self._handle_recipe_relation(
            request, pk, FavoriteRecipe,
            {'already_exists': 'Рецепт "{recipe}" уже в избранном'}
        )

    @action(
        detail=True, 
        methods=['get'], 
        url_path='get-link',
        permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    )
    def get_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт"""
        recipe = self.get_object()
        
        # Импортируем функцию генерации короткой ссылки
        from recipes.views import generate_short_link
        
        short_id = generate_short_link(recipe.id)
        if not short_id:
            return Response(
                {'error': 'Не удалось создать короткую ссылку'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Формируем полную ссылку
        short_link = request.build_absolute_uri(f'/recipes/{short_id}/')
        
        return Response({'short-link': short_link})


class UserViewSet(DjoserUserViewSet):
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(
        detail=False, 
        methods=['get'], 
        url_path='me', 
        permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request, *args, **kwargs):
        """Получить текущего пользователя"""
        return super().me(request, *args, **kwargs)

    @action(
        detail=False, 
        methods=['put', 'delete'], 
        url_path='me/avatar', 
        permission_classes=[permissions.IsAuthenticated]
    )
    def avatar(self, request):
        """Управление аватаром пользователя"""
        user_instance = request.user
        
        if request.method == 'PUT':
            serializer = self.get_serializer(
                user_instance, 
                data=request.data, 
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            
            avatar_data = request.data.get('avatar')
            if not avatar_data:
                return Response(
                    {'avatar': 'Поле avatar обязательно для заполнения!'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if user_instance.avatar:
                user_instance.avatar.delete()
            
            serializer.save()
            return Response(
                {'avatar': serializer.data['avatar']}, 
                status=status.HTTP_200_OK
            )
        
        if not user_instance.avatar:
            return Response(
                {'detail': 'У пользователя нет аватара'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_instance.avatar.delete()
        user_instance.save()
        return Response(
            {'message': 'Аватар успешно удален'}, 
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False, 
        methods=['get'], 
        url_path='subscriptions',
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получить список подписок пользователя"""
        subscribed_users = User.objects.filter(
            followers__subscriber=request.user
        ).prefetch_related('authored_recipes')
        
        page = self.paginate_queryset(subscribed_users)
        if page is not None:
            serializer = UserSubscriptionSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = UserSubscriptionSerializer(subscribed_users, many=True, context={'request': request})
        return Response(serializer.data)

    @action(
        detail=True, 
        methods=['post', 'delete'], 
        url_path='subscribe',
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        """Подписаться/отписаться от пользователя"""
        target_user = get_object_or_404(User, pk=pk)
        
        if request.method == 'POST':
            if target_user == request.user:
                return Response(
                    {'detail': 'Нельзя подписаться на самого себя'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            _, created = UserSubscription.objects.get_or_create(
                subscriber=request.user, 
                target_user=target_user
            )
            if not created:
                return Response(
                    {'detail': f'Вы уже подписаны на пользователя {target_user.username}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = UserSubscriptionSerializer(target_user, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        subscription = get_object_or_404(
            UserSubscription, 
            subscriber=request.user, 
            target_user=target_user
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
