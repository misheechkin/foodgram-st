from django.contrib import admin
from .models import Profile, Follow
from django.contrib.auth.admin import UserAdmin


admin.site.register(Profile,UserAdmin)
admin.site.register(Follow)
