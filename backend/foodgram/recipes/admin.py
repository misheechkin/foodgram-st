from django.contrib import admin
from .models import Recipe, Ingredient, IngredientRecipe


admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(IngredientRecipe)