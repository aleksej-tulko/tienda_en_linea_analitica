from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import create_or_get_token, remove_token, UsersViewSet

users_router = DefaultRouter()

users_router.register('users', UsersViewSet, basename='users')

api_v1_urls = [
    path('auth/token/login/', create_or_get_token, name='login'),
    path('auth/token/logout/', remove_token, name='logout'),
    *users_router.urls,
]

urlpatterns = [
    path('api/', include(api_v1_urls)),
]
