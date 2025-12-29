from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response

from api.permissions import IsAuthenticatedOrReadOnlyOrCreateUser
from api.validators import regex_email

User = get_user_model()


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
