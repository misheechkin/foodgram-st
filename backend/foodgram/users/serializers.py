import base64
from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import Profile, Follow


class Base64PicField(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            header, encoded = data.split(';base64,')
            ext = header.split('/')[-1]
            data = ContentFile(base64.b64decode(encoded), name=f"pic.{ext}")
        return super().to_internal_value(data)


class RelationshipSerializer(serializers.ModelSerializer):

    class Meta:
        model = Follow
        fields = ['author', 'subscriber']
        read_only_fields = ['author', 'subscriber']


class MemberSerializer(serializers.ModelSerializer):

    image = Base64PicField(source='avatar', required=False, allow_null=True)
    image_url = serializers.SerializerMethodField(read_only=True)
    total_followers = serializers.SerializerMethodField(read_only=True)
    total_following = serializers.SerializerMethodField(read_only=True)
    is_following = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'image', 'image_url',
            'total_followers', 'total_following', 'is_following'
        ]
        read_only_fields = ['image_url', 'total_followers', 'total_following', 'is_following']

    def get_image_url(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'url'):
            req = self.context.get('request')
            return req.build_absolute_uri(obj.avatar.url) if req else obj.avatar.url
        return None

    def get_total_followers(self, obj):
        return obj.followers.count()

    def get_total_following(self, obj):
        return obj.subscriptions.count()

    def get_is_following(self, obj):
        req = self.context.get('request')
        user = getattr(req, 'user', None)
        if user and user.is_authenticated:
            return Follow.objects.filter(author=obj, subscriber=user).exists()
        return False

    def update(self, instance, validated_data):
        img = validated_data.pop('avatar', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if img is not None:
            instance.avatar = img
        instance.save()
        return instance

    def create(self, validated_data):
        return Profile.objects.create(**validated_data)