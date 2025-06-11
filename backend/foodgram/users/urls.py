from django.urls import include, path

urlpatterns = [
    path('', include('djoser.urls.base')),
    path('auth/', include('djoser.urls.authtoken')),
    path('auth/', include('djoser.urls.jwt')),
]