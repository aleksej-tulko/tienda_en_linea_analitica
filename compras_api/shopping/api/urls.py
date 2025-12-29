from django.urls import include, path

from api.views import create_or_get_token, remove_token

api_v1_urls = [
    path('auth/token/login/', create_or_get_token, name='login'),
    path('auth/token/logout/', remove_token, name='logout'),
]

urlpatterns = [
    path('api/', include(api_v1_urls)),
]
