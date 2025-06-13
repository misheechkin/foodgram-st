from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ProductComponentViewSet,
    CookingRecipeViewSet,
    UserSubscriptionsViewSet,
    SubscriptionManagementViewSet
)

router = DefaultRouter()
router.register(r'recipes', CookingRecipeViewSet, basename='cooking-recipes')
router.register(r'ingredients', ProductComponentViewSet)
router.register(
    r'users/subscriptions',
    UserSubscriptionsViewSet,
    basename='user-subscriptions'
)
router.register(r'users', SubscriptionManagementViewSet, basename='subscription-management')

urlpatterns = [
    path('', include(router.urls)),
]