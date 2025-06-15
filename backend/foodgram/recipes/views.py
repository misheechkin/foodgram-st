from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import CookingRecipe


def redirect_to_recipe(request, short_id):
    """
    Обработчик для коротких ссылок на рецепты.
    Преобразует короткий ID в полную ссылку на рецепт.
    """
    try:
        # Декодируем короткий ID обратно в ID рецепта
        # Простая реализация: короткий ID = base36 от ID рецепта
        recipe_id = int(short_id, 36)
        recipe = get_object_or_404(CookingRecipe, id=recipe_id)
        
        # Перенаправляем на детальную страницу рецепта в API
        return HttpResponseRedirect(f'/api/recipes/{recipe.id}/')
        
    except (ValueError, TypeError):
        # Если не удалось декодировать короткий ID
        from django.http import Http404
        raise Http404(_('Некорректная короткая ссылка'))


def generate_short_link(recipe_id):
    """
    Генерирует короткую ссылку для рецепта.
    Преобразует ID рецепта в base36 формат.
    """
    try:
        # Конвертируем ID в base36 для получения короткой строки
        import math
        
        if recipe_id <= 0:
            return None
            
        def to_base36(num):
            alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
            if num == 0:
                return alphabet[0]
            
            base36 = ""
            while num:
                num, remainder = divmod(num, 36)
                base36 = alphabet[remainder] + base36
            return base36
        
        return to_base36(recipe_id)
        
    except (ValueError, TypeError):
        return None