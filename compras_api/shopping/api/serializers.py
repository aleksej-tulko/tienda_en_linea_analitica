from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.constants import (
    GET_USER_FIELDS,
    POST_USER_FIELDS,
)
from api.validators import prohibited_usernames, regex_username
from users.models import ApiUser

User = get_user_model()


class ReadUserSerializer(serializers.ModelSerializer):
    """User serializer for read operations."""

    class Meta:
        model = User
        fields = GET_USER_FIELDS


class WriteUserSerializer(serializers.ModelSerializer):
    """User serializer for write operations."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = POST_USER_FIELDS

    def validate_username(self, username: str) -> str:
        """Validates username."""

        prohibited_usernames(username)
        regex_username(username)
        return username

    def create(self, validated_data: dict) -> ApiUser:
        """Creates a new user with a hashed password."""

        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        user.password = password
        return user
