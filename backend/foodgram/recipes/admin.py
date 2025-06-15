from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from .models import (
    CookingRecipe, ProductComponent, RecipeComponent, 
    FavoriteRecipe, ShoppingCart, User, UserSubscription
)


class HasRecipesFilter(admin.SimpleListFilter):
    title = _('наличие рецептов')
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Есть рецепты')),
            ('no', _('Нет рецептов')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(authored_recipes__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(authored_recipes__isnull=True).distinct()


class HasSubscriptionsFilter(admin.SimpleListFilter):
    title = _('наличие подписок')
    parameter_name = 'has_subscriptions'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Есть подписки')),
            ('no', _('Нет подписок')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(following__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(following__isnull=True).distinct()


class HasSubscribersFilter(admin.SimpleListFilter):
    title = _('наличие подписчиков')
    parameter_name = 'has_subscribers'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Есть подписчики')),
            ('no', _('Нет подписчиков')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(followers__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(followers__isnull=True).distinct()


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    
    list_display = (
        'id', 'username', 'get_full_name', 'email', 
        'get_avatar', 'recipes_count', 'subscribers_count', 
        'subscriptions_count'
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = (
        'is_staff', 'is_active', 'date_joined', 
        HasRecipesFilter, HasSubscriptionsFilter, HasSubscribersFilter
    )
    ordering = ('username',)
    readonly_fields = (
        'date_joined', 'last_login', 'recipes_count', 
        'subscribers_count', 'subscriptions_count', 'get_avatar'
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'authored_recipes', 'following', 'followers'
        )
    
    def get_full_name(self, user):
        """ФИО пользователя"""
        return f"{user.first_name} {user.last_name}".strip() or user.username
    get_full_name.short_description = _('ФИО')
    get_full_name.admin_order_field = 'first_name'
    
    def recipes_count(self, user):
        """Количество рецептов пользователя"""
        return user.authored_recipes.count()
    recipes_count.short_description = _('Количество рецептов')
    recipes_count.admin_order_field = 'authored_recipes'
    
    def subscribers_count(self, user):
        """Количество подписчиков"""
        return user.followers.count()
    subscribers_count.short_description = _('Подписчиков')
    subscribers_count.admin_order_field = 'followers'
    
    def subscriptions_count(self, user):
        """Количество подписок"""
        return user.following.count()
    subscriptions_count.short_description = _('Подписок')
    subscriptions_count.admin_order_field = 'following'
    
    @mark_safe
    def get_avatar(self, user):
        """Отображение аватара в админке"""
        if user.avatar:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                user.avatar.url
            )
        return _('Нет аватара')
    get_avatar.short_description = _('Аватар')
    
    def has_recipes(self, user):
        """Фильтр: есть рецепты"""
        return user.authored_recipes.exists()
    has_recipes.boolean = True
    has_recipes.short_description = _('Есть рецепты')
    
    def has_subscriptions(self, user):
        """Фильтр: есть подписки"""
        return user.following.exists()
    has_subscriptions.boolean = True
    has_subscriptions.short_description = _('Есть подписки')
    
    def has_subscribers(self, user):
        """Фильтр: есть подписчики"""
        return user.followers.exists()
    has_subscribers.boolean = True
    has_subscribers.short_description = _('Есть подписчики')


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    
    list_display = (
        'subscriber', 'target_user', 'get_subscriber_email', 
        'get_target_email', 'get_subscription_info'
    )
    search_fields = (
        'subscriber__email', 'target_user__email', 
        'subscriber__username', 'target_user__username'
    )
    list_filter = ('subscriber', 'target_user')
    ordering = ('subscriber',)
    
    def get_subscriber_email(self, obj):
        """Email подписчика"""
        return obj.subscriber.email
    get_subscriber_email.short_description = _('Email подписчика')
    get_subscriber_email.admin_order_field = 'subscriber__email'
    
    def get_target_email(self, obj):
        """Email целевого пользователя"""
        return obj.target_user.email
    get_target_email.short_description = _('Email автора')
    get_target_email.admin_order_field = 'target_user__email'
    
    def get_subscription_info(self, obj):
        """Дополнительная информация о подписке"""
        target_recipes = obj.target_user.authored_recipes.count()
        return f"{target_recipes} {_('рецептов')}"
    get_subscription_info.short_description = _('Рецептов у автора')


@admin.register(ProductComponent)
class ProductComponentAdmin(admin.ModelAdmin):
    
    list_display = ('title', 'unit_type')
    search_fields = ('title', 'unit_type')
    list_filter = ('unit_type',)
    ordering = ('title',)


@admin.register(CookingRecipe)
class CookingRecipeAdmin(admin.ModelAdmin):
    
    list_display = (
        'id', 'title', 'cook_duration', 'creator', 
        'favorites_count', 'get_ingredients', 'get_image'
    )
    search_fields = ('title', 'creator__email', 'creator__username')
    list_filter = ('creator', 'date_created')
    ordering = ('-date_created',)
    readonly_fields = ('date_created', 'get_ingredients', 'get_image', 'favorites_count')
    
    @mark_safe
    def get_ingredients(self, obj):
        """Отображение продуктов в админке"""
        ingredients = obj.recipe_components.select_related('component')
        if not ingredients:
            return _('Нет продуктов')
        
        ingredients_list = []
        for ingredient in ingredients:
            ingredients_list.append(
                f"{ingredient.component.title} - {ingredient.quantity} {ingredient.component.unit_type}"
            )
        
        return format_html(
            '<ul>{}</ul>',
            format_html(''.join('<li>{}</li>' for _ in ingredients_list), *ingredients_list)
        )
    get_ingredients.short_description = _('Продукты')
    
    @mark_safe
    def get_image(self, obj):
        """Отображение картинки в админке"""
        if obj.picture:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 5px;" />',
                obj.picture.url
            )
        return _('Нет изображения')
    get_image.short_description = _('Изображение')
    
    def favorites_count(self, obj):
        """Количество добавлений в избранное"""
        return obj.favorites.count()
    favorites_count.short_description = _('В избранном')
    favorites_count.admin_order_field = 'favorites'


@admin.register(RecipeComponent)
class RecipeComponentAdmin(admin.ModelAdmin):
    
    list_display = ('recipe', 'component', 'quantity')
    search_fields = ('recipe__title', 'component__title')
    list_filter = ('recipe', 'component')
    ordering = ('recipe',)


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    
    list_display = ('user', 'recipe', 'get_recipe_title')
    search_fields = ('user__email', 'user__username', 'recipe__title')
    list_filter = ('recipe__creator', 'recipe__date_created')
    ordering = ('-id',)
    
    def get_recipe_title(self, obj):
        """Название рецепта для удобства"""
        return obj.recipe.title
    get_recipe_title.short_description = _('Название рецепта')
    get_recipe_title.admin_order_field = 'recipe__title'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    
    list_display = ('user', 'recipe', 'get_recipe_title', 'get_recipe_author')
    search_fields = ('user__email', 'user__username', 'recipe__title')
    list_filter = ('recipe__creator', 'recipe__date_created')
    ordering = ('-id',)
    
    def get_recipe_title(self, obj):
        """Название рецепта для удобства"""
        return obj.recipe.title
    get_recipe_title.short_description = _('Название рецепта')
    get_recipe_title.admin_order_field = 'recipe__title'
    
    def get_recipe_author(self, obj):
        """Автор рецепта для удобства"""
        return obj.recipe.creator.get_full_name() or obj.recipe.creator.username
    get_recipe_author.short_description = _('Автор рецепта')
    get_recipe_author.admin_order_field = 'recipe__creator'


# Кастомизация главной страницы админки
class CustomAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Добавляем статистику рецептов
        recipe_stats = {
            'total_recipes': CookingRecipe.objects.count(),
            'total_users': User.objects.count(),
            'total_ingredients': ProductComponent.objects.count(),
            'recipes_in_favorites': FavoriteRecipe.objects.values('recipe').distinct().count(),
            'recipes_in_carts': ShoppingCart.objects.values('recipe').distinct().count(),
        }
        
        extra_context['recipe_stats'] = recipe_stats
        return super().index(request, extra_context)

# Переопределение стандартного админ-сайта (опционально)
# admin.site = CustomAdminSite()


# Добавляем счетчик рецептов в заголовок админки
admin.site.site_header = _('Администрирование Foodgram')
admin.site.site_title = _('Foodgram Admin')
admin.site.index_title = _('Добро пожаловать в админ-панель Foodgram')