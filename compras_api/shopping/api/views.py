from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from api.constants import PASSWORD_NAME, PASSWORD_URI
from api.mixin import BaseReadOnlyViewSet
from api.permissions import IsAuthenticatedOrReadOnlyOrCreateUser
from api.serializers import (
    BrandSerializer,
    ChangePasswordSerializer,
    CategorySerializer,
    CompraSerializer,
    ProductSerializer,
    ReadUserSerializer,
    TagSerializer,
    WriteUserSerializer
)
from api.validators import regex_email
from gastos.models import Brand, Category, Compra, Product, Tag

User = get_user_model()


class UsersViewSet(viewsets.ModelViewSet):

    permission_classes = (IsAuthenticatedOrReadOnlyOrCreateUser,)

    def get_serializer_class(self) -> type[Serializer]:
        """Selects the appropriate serializer class."""

        return (WriteUserSerializer if self.action in ('create',)
                else ReadUserSerializer)

    @action(detail=False, url_path=settings.PERSONAL_PAGE_URL,
            url_name=settings.PERSONAL_PAGE_URL,
            permission_classes=(IsAuthenticated,),
            methods=('GET',))
    def get_personal_page(self, request: Request) -> Response:
        return Response(
            self.get_serializer(request.user).data, status=status.HTTP_200_OK
        )

    @action(
        detail=False, url_path=PASSWORD_URI, url_name=PASSWORD_NAME,
        permission_classes=(IsAuthenticated,), methods=('post',)
    )
    def change_password(self, request: Request, pk=None) -> Response:
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.update(request.user, serializer.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes((IsAuthenticatedOrReadOnlyOrCreateUser,))
def create_or_get_token(request: Request) -> Response:
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
    request.user.auth_token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class BrandsViewSet(BaseReadOnlyViewSet):

    queryset = Brand.objects.all()
    serializer_class = BrandSerializer


class CategoriesViewSet(BaseReadOnlyViewSet):

    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductsViewSet(BaseReadOnlyViewSet):

    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class TagsViewSet(BaseReadOnlyViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class ComprasViewSet(viewsets.ModelViewSet):

    queryset = Compra.objects.all().prefetch_related('products', 'tags')
    serializer_class = CompraSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    search_fields = ('name',)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return super().create(request, *args, **kwargs)
