from base64 import b64decode
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers
from djoser.serializers import UserSerializer, UserCreateSerializer

from .models import User, UserSubscription


class Base64AvatarField(serializers.ImageField):
    
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format_part, image_data = data.split(';base64,')
            extension = format_part.split('/')[-1]
            file_name = f"avatar_{uuid.uuid4().hex[:8]}.{extension}"
            data = ContentFile(b64decode(image_data), name=file_name)
        return super().to_internal_value(data)


class UserSerializer(UserSerializer):
    
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = Base64AvatarField(required=False, allow_null=True)

    class Meta(UserSerializer.Meta):
        model = User
        fields = [
            'id', 'email', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or obj == request.user:
            return False
        return UserSubscription.objects.filter(
            subscriber=request.user, 
            target_user=obj
        ).exists()


class UserCreateSerializer(UserCreateSerializer):
    
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'password', 'first_name', 'last_name')
