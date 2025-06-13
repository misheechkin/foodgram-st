from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, UserSubscription


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    ordering = ('email',)
    readonly_fields = ('date_joined', 'last_login')


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    
    list_display = ('subscriber', 'target_user')
    search_fields = ('subscriber__email', 'target_user__email', 'subscriber__username', 'target_user__username')
    list_filter = ('subscriber', 'target_user')
    ordering = ('subscriber',)
