from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile, Subscription

admin.site.register(UserProfile, UserAdmin)
admin.site.register(Subscription)
