from io import BytesIO
from django.db.models import Sum
from django.http import FileResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import filters, viewsets, permissions, mixins, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import CookingRecipe, ProductComponent, ShoppingCart, RecipeComponent, FavoriteRecipe
from .serializers import ProductSerializer, CookingRecipeSerializer, CookingRecipeShortSerializer, UserSubscriptionSerializer
from .permissions import CreatorOrReadOnly
from .filters import CookingRecipeFilter
from users.models import UserSubscription

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
            .prefetch_related('recipe_components__component', 'favorited_by', 'in_shopping_carts')
            .order_by('-date_created')
        )

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(
        detail=True, 
        methods=['post', 'delete'], 
        url_path='shopping-cart',
        permission_classes=[permissions.IsAuthenticated]
    )
    def handle_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(CookingRecipe, pk=pk)
        user = request.user
        
        if request.method == 'POST':
            _, created = ShoppingCart.objects.get_or_create(customer=user, recipe=recipe)
            if not created:
                return Response({'detail': 'Рецепт уже в корзине'}, status=status.HTTP_400_BAD_REQUEST)
            serializer = CookingRecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        deleted_count, _ = ShoppingCart.objects.filter(customer=user, recipe=recipe).delete()
        if deleted_count == 0:
            return Response({'detail': 'Рецепт не был в корзине'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)    @action(
        detail=False, 
        methods=['get'], 
        url_path='download-shopping-list',
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_list(self, request):
        user = request.user
        shopping_list = (
            RecipeComponent.objects
            .filter(recipe__in_shopping_carts__customer=user)
            .values('component__title', 'component__unit_type')
            .annotate(total_quantity=Sum('quantity'))
            .order_by('component__title')
        )
        
        if not shopping_list:
            return Response({'detail': 'Корзина покупок пуста'}, status=status.HTTP_200_OK)
        
        file_buffer = BytesIO()
        for item in shopping_list:
            line = f"{item['component__title']} - {item['total_quantity']} {item['component__unit_type']}\n"
            file_buffer.write(line.encode('utf-8'))
        
        file_buffer.seek(0)
        return FileResponse(
            file_buffer, 
            as_attachment=True, 
            filename='shopping_list.txt', 
            content_type='text/plain; charset=utf-8'
        )    @action(
        detail=True, 
        methods=['post', 'delete'], 
        url_path='favorite',
        permission_classes=[permissions.IsAuthenticated]
    )
    def handle_favorites(self, request, pk=None):
        recipe = get_object_or_404(CookingRecipe, pk=pk)
        user = request.user
        
        if request.method == 'POST':
            _, created = FavoriteRecipe.objects.get_or_create(owner=user, recipe=recipe)
            if not created:
                return Response({'detail': 'Рецепт уже в избранном'}, status=status.HTTP_400_BAD_REQUEST)
            serializer = CookingRecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        deleted_count, _ = FavoriteRecipe.objects.filter(owner=user, recipe=recipe).delete()
        if deleted_count == 0:
            return Response({'detail': 'Рецепт не был в избранном'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserSubscriptionsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    
    serializer_class = UserSubscriptionSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return UserModel.objects.filter(
            followers__subscriber=self.request.user
        ).prefetch_related('authored_recipes')


class SubscriptionManagementViewSet(viewsets.GenericViewSet):
    
    queryset = UserModel.objects.all()
    serializer_class = UserSubscriptionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def manage_subscription(self, request, pk=None):
        target_user = get_object_or_404(UserModel, pk=pk)
        
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
                    {'detail': 'Вы уже подписаны на этого пользователя'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = UserSubscriptionSerializer(target_user, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        deleted_count, _ = UserSubscription.objects.filter(
            subscriber=request.user, 
            target_user=target_user
        ).delete()
        
        if deleted_count == 0:
            return Response(
                {'detail': 'Вы не были подписаны на этого пользователя'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(status=status.HTTP_204_NO_CONTENT)