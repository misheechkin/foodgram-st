from base64 import b64decode
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers
from djoser.serializers import UserSerializer, UserCreateSerializer

from .models import UserProfile, Subscription


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            filename = f"avatar_{uuid.uuid4().hex[:8]}.{ext}"
            data = ContentFile(b64decode(imgstr), name=filename)
        return super().to_internal_value(data)


class UserProfileSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta(UserSerializer.Meta):
        model = UserProfile
        fields = [
            'id', 'email', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or obj == request.user:
            return False
        return Subscription.objects.filter(user=request.user, follows=obj).exists()


class UserProfileCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = UserProfile
        fields = ('id', 'email', 'username', 'password', 'first_name', 'last_name')
