from rest_framework import status, permissions, pagination
from rest_framework.decorators import action
from rest_framework.response import Response
from djoser.views import UserViewSet

from .models import User
from .serializers import UserSerializer


class UserViewSet(UserViewSet):
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = pagination.LimitOffsetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(
        detail=False, 
        methods=['get'], 
        url_path='me', 
        permission_classes=[permissions.IsAuthenticated]
    )
    def get_current_user(self, request):
        serializer_data = self.get_serializer(request.user).data
        return Response(serializer_data)

    @action(
        detail=True, 
        methods=['get'], 
        url_path='', 
        permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    )
    def retrieve_user_profile(self, request, pk=None):
        user_instance = self.get_object()
        serializer_data = self.get_serializer(user_instance).data
        return Response(serializer_data, status=status.HTTP_200_OK)

    @action(
        detail=False, 
        methods=['put', 'delete'], 
        url_path='me/avatar', 
        permission_classes=[permissions.IsAuthenticated]
    )
    def manage_avatar(self, request):
        user_instance = request.user
        
        if request.method == 'PUT':
            serializer = self.get_serializer(
                user_instance, 
                data=request.data, 
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            
            avatar_data = request.data.get('avatar')
            if not avatar_data:
                return Response(
                    {'avatar': 'Поле avatar обязательно для заполнения!'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if user_instance.avatar:
                user_instance.avatar.delete()
            
            serializer.save()
            return Response(
                {'avatar': serializer.data['avatar']}, 
                status=status.HTTP_200_OK
            )
        
        if not user_instance.avatar:
            return Response(
                {'detail': 'У пользователя нет аватара'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_instance.avatar.delete()
        user_instance.save()
        return Response(
            {'message': 'Аватар успешно удален'}, 
            status=status.HTTP_204_NO_CONTENT
        )