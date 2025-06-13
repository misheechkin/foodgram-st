from django.contrib import admin
from .models import CookingRecipe, ProductComponent, RecipeComponent


@admin.register(ProductComponent)
class ProductComponentAdmin(admin.ModelAdmin):
    
    list_display = ('title', 'unit_type')
    search_fields = ('title',)
    list_filter = ('unit_type',)
    ordering = ('title',)


@admin.register(CookingRecipe)
class CookingRecipeAdmin(admin.ModelAdmin):
    
    list_display = ('title', 'creator', 'cook_duration', 'date_created')
    search_fields = ('title', 'creator__email', 'creator__username')
    list_filter = ('creator', 'date_created')
    ordering = ('-date_created',)
    readonly_fields = ('date_created',)


@admin.register(RecipeComponent)
class RecipeComponentAdmin(admin.ModelAdmin):
    
    list_display = ('recipe', 'component', 'quantity')
    search_fields = ('recipe__title', 'component__title')
    list_filter = ('recipe', 'component')
    ordering = ('recipe',)