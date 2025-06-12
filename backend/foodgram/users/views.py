from rest_framework import viewsets, mixins, permissions, pagination
from .models import Profile, Follow
from .serializers import FollowSerializer, ProfileSerializer
from rest_framework.response import Response
from rest_framework import viewsets, pagination, mixins, permissions, status

class FollowViewSet(viewsets.GenericViewSet,
                    mixins.CreateModelMixin,
                    mixins.DestroyModelMixin):
    queryset = Follow.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        return Follow.objects.filter(subscriber=self.request.user)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = FollowSerializer
    pagination_class = pagination.LimitOffsetPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save()

    def get_queryset(self):
        return Profile.objects.all()
    
    @action(detail=False, methods=['get'], url_path='me')
    def retrieve_current_user(self, request):
        serializer = self.get_serializer(instance=request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def manage_avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            serializer = self.get_serializer(instance=user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            existing_avatar = getattr(user, 'avatar', None)
            if existing_avatar:
                existing_avatar.delete()

            serializer.save()
            avatar_url = serializer.data.get('avatar')
            return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)

        if user.avatar:
            user.avatar.delete()
            user.save()

        return Response({'message': 'Аватар удалён успешно'}, status=status.HTTP_204_NO_CONTENT)
