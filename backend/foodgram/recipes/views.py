from io import BytesIO
from django.db.models import Sum
from django.http import FileResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import  filters, viewsets, permissions, mixins, status
from rest_framework.pagination import (PageNumberPagination,
                                       LimitOffsetPagination)
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Recipe, Ingredient, CartItem, IngredientRecipe, Favorites
from .serializers import IngredientSerializer, RecipeSerializer, ShortRecipeSerializer, SubscriptionSerializer
from .permissions import AuthorOrReadOnly
from .filters import RecipeFilter
from users.models import Subscription

User = get_user_model()

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('name',)
    search_fields = ('^name',)

    def get_queryset(self):
        term = self.request.query_params.get('name')
        if term:
            return self.queryset.filter(name__istartswith=term)
        return self.queryset

class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (AuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('name',)
    filterset_class = RecipeFilter

    def get_queryset(self):
        return (
            Recipe.objects
                  .select_related('author')
                  .prefetch_related(
                      'recipe_ingredients__ingredient',
                      'user_favs',
                      'shopping_carts'
                  )
                  .order_by('-created_at')
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'], url_path='cart', permission_classes=[permissions.IsAuthenticated])
    def manage_cart(self, request, pk=None):
        recipe_obj = get_object_or_404(Recipe, pk=pk)
        user_obj = request.user
        if request.method == 'POST':
            _, added = CartItem.objects.get_or_create(user=user_obj, recipe=recipe_obj)
            if not added:
                return Response({'detail': 'Уже в корзине'}, status=status.HTTP_400_BAD_REQUEST)
            serializer = ShortRecipeSerializer(recipe_obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        removed, _ = CartItem.objects.filter(user=user_obj, recipe=recipe_obj).delete()
        if removed == 0:
            return Response({'detail': 'Не было в корзине'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='download-cart', permission_classes=[permissions.IsAuthenticated])
    def download_cart(self, request):
        user_obj = request.user
        items = (
            IngredientRecipe.objects
            .filter(recipe__shopping_carts__user=user_obj)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total=Sum('amount'))
            .order_by('ingredient__name')
        )
        if not items:
            return Response({'detail': 'Корзина пуста'}, status=status.HTTP_200_OK)
        buffer = BytesIO()
        for entry in items:
            buffer.write(
                f"{entry['ingredient__name']} - {entry['total']} {entry['ingredient__measurement_unit']}\n".encode('utf-8')
            )
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='shopping_list.txt', content_type='text/plain')

    @action(detail=True, methods=['post', 'delete'], url_path='favorite', permission_classes=[permissions.IsAuthenticated])
    def manage_favorites(self, request, pk=None):
        recipe_obj = get_object_or_404(Recipe, pk=pk)
        user_obj = request.user
        if request.method == 'POST':
            _, added = Favorites.objects.get_or_create(user=user_obj, recipe=recipe_obj)
            if not added:
                return Response({'detail': 'Уже в избранном'}, status=status.HTTP_400_BAD_REQUEST)
            serializer = ShortRecipeSerializer(recipe_obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        removed, _ = Favorites.objects.filter(user=user_obj, recipe=recipe_obj).delete()
        if removed == 0:
            return Response({'detail': 'Не было в избранном'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

class SubscriptionViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = SubscriptionSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return User.objects.filter(subbed_to__user=self.request.user).prefetch_related('recipes')

class SingleSubscriptionViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def toggle_sub(self, request, pk=None):
        target = get_object_or_404(User, pk=pk)
        if request.method == 'POST':
            if target == request.user:
                return Response({'detail': 'Нельзя на себя'}, status=status.HTTP_400_BAD_REQUEST)
            _, created = Subscription.objects.get_or_create(user=request.user, follows=target)
            if not created:
                return