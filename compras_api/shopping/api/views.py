from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from api.constants import PASSWORD_NAME, PASSWORD_URI
from api.permissions import IsAuthenticatedOrReadOnlyOrCreateUser
from api.serializers import (
    ChangePasswordSerializer,
    ReadUserSerializer,
    WriteUserSerializer
)
from api.validators import regex_email

User = get_user_model()


class UsersViewSet(viewsets.ModelViewSet):
    """
    Mixin for auxiliary methods and overriding
    built-in viewset methods for user management.
    """

    def get_serializer_class(self) -> type[Serializer]:
        """Selects the appropriate serializer class."""

        return (WriteUserSerializer if self.action in ('create',)
                else ReadUserSerializer)

    @action(
        detail=False, url_path=PASSWORD_URI, url_name=PASSWORD_NAME,
        permission_classes=(IsAuthenticated,), methods=('post',)
    )
    def change_password(self, request: Request, pk=None) -> Response:
        """
        Change the authenticated user's password.

        Args:
            request (Request): The HTTP request object containing
            old and new passwords.

        Returns:
            Response: Empty response with a 204 status code.
        """

        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.update(request.user, serializer.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes((IsAuthenticatedOrReadOnlyOrCreateUser,))
def create_or_get_token(request: Request) -> Response:
    """
    Generate or retrieve an authentication token for a user.

    Args:
        request (Request): The HTTP request object containing
        email and password.

    Returns:
        Response: Authentication token if credentials are valid,
        400 status code otherwise.
    """

    if 'email' in request.data and 'password' in request.data:
        password = request.data['password']
        email = regex_email(email=request.data['email'])
        user = get_object_or_404(User.objects.filter(email=email))
        auth_user = authenticate(email=user.email, password=password)
        token, _ = Token.objects.get_or_create(user=auth_user)
        return Response({'auth_token': token.key}, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def remove_token(request: Request) -> Response:
    """
    Remove the authentication token of the authenticated user.

    Args:
        request (Request): The HTTP request object.

    Returns:
        Response: Empty response with a 204 status code.
    """

    request.user.auth_token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
