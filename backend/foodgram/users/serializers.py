from django.contrib.auth import get_user_model
from rest_framework import serializers
from recipes.serializers import Base64ImageField

from .models import Profile, Follow

User = get_user_model()


class FollowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Follow
        fields = ('author', 'subscriber')
        read_only_fields = ('author', 'subscriber')


class ProfileSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(required=False, allow_null=True)
    avatar_url = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = (
            'id', 'username', 'first_name', 'last_name', 'email',
            'avatar', 'avatar_url', 'is_following',
        )
        read_only_fields = ('is_following',)

    def get_avatar_url(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return obj.avatar.url
        return None

    def get_is_following(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Follow.objects.filter(
            author=obj,
            subscriber=request.user
        ).exists()

    def update(self, instance, validated_data):
        avatar = validated_data.get('avatar')
        if avatar is not None:
            instance.avatar = avatar
            instance.save()
        return instance

    def delete_avatar(self):
        instance = self.instance
        if instance.avatar:
            instance.avatar.delete(save=True)
        return instance

    