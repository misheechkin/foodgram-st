from django.urls import include, path


urlpatterns = [
    path('', include('users.urls')),
    path('', include('recipes.urls')),
]