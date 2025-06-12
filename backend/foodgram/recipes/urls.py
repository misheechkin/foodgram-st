from django.urls import include, path
from rest_framework import routers

from .views import (IngredientViewSet,
                    RecipeViewSet,
                    SubscriptionViewSet,
                    SingleSubscriptionViewSet)

router = routers.DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients', IngredientViewSet)
router.register(r'users/subscriptions',
                SubscriptionViewSet,
                basename='subscriptions')
router.register(r'users', SingleSubscriptionViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
]