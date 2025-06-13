from django.shortcuts import get_object_or_404
from rest_framework import status, permissions, pagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.validators import ValidationError
from djoser.views import UserViewSet

from .models import UserProfile, Subscription
from .serializers import UserProfileSerializer


class UserProfileViewSet(UserViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    pagination_class = pagination.LimitOffsetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'], url_path='me', permission_classes=[permissions.IsAuthenticated])
    def get_current_user(self, request):
        data = self.get_serializer(request.user).data
        return Response(data)

    @action(detail=True, methods=['get'], url_path='', permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def get_user(self, request, pk=None):
        user = self.get_object()
        data = self.get_serializer(user).data
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar', permission_classes=[permissions.IsAuthenticated])
    def put_delete_avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            avatar = request.data.get('avatar')
            if not avatar:
                return Response({'avatar': 'Поле avatar не задано!'}, status=status.HTTP_400_BAD_REQUEST)
            if user.avatar:
                user.avatar.delete()
            serializer.save()
            return Response({'avatar': serializer.data['avatar']}, status=status.HTTP_200_OK)
        if not user.avatar:
            return Response({'detail': 'Аватар отсутствует'}, status=status.HTTP_400_BAD_REQUEST)
        user.avatar.delete()
        user.save()
        return Response({'message': 'Аватар удалён'}, status=status.HTTP_204_NO_CONTENT)