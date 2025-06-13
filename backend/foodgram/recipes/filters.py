from .models import CookingRecipe
from django_filters import rest_framework as filters


class CookingRecipeFilter(filters.FilterSet):
    
    is_favorited = filters.BooleanFilter(method='filter_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_in_cart')

    class Meta:
        model = CookingRecipe
        fields = ['creator', 'title']

    def filter_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorited_by__owner=self.request.user)
        return queryset

    def filter_in_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(in_shopping_carts__customer=self.request.user)
        return queryset