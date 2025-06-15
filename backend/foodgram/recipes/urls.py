from django.urls import path
from . import views

# URLs для коротких ссылок на рецепты
urlpatterns = [
    path('<str:short_id>/', views.redirect_to_recipe, name='short-link'),
]