from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    create_or_get_token,
    remove_token,
    BrandsViewSet,
    CategoriesViewSet,
    ComprasViewSet,
    ProductsViewSet,
    TagsViewSet,
    UsersViewSet
)

users_router = DefaultRouter()

compras_router = DefaultRouter()

users_router.register('users', UsersViewSet, basename='users')

compras_router.register('brands', BrandsViewSet, basename='brands')
compras_router.register('categories', CategoriesViewSet, basename='categories')
compras_router.register('compras', ComprasViewSet, basename='compras')
compras_router.register('products', ProductsViewSet, basename='products')
compras_router.register('tags', TagsViewSet, basename='tags')

api_v1_urls = [
    path('auth/token/login/', create_or_get_token, name='login'),
    path('auth/token/logout/', remove_token, name='logout'),
    *users_router.urls,
    *compras_router.urls
]

urlpatterns = [
    path('api/', include(api_v1_urls)),
]
