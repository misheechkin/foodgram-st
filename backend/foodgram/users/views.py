from rest_framework import viewsets, mixins, permissions, pagination
from .models import Profile, Follow
from .serializers import MemberSerializer, RelationshipSerializer


class FollowViewSet(viewsets.GenericViewSet,
                    mixins.CreateModelMixin,
                    mixins.DestroyModelMixin):
    queryset = Follow.objects.all()
    serializer_class = RelationshipSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        return Follow.objects.filter(subscriber=self.request.user)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = MemberSerializer
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
