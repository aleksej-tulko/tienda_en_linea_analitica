from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.constants import (
    GET_USER_FIELDS,
    POST_USER_FIELDS,
)
from api.validators import prohibited_usernames, regex_username
from users.models import ApiUser

INCORRECT_CURRENT_PASSWORD = 'Incorrect current password.'
NEW_PASSWORD_IS_SAME = 'The new password must not be the same as the old one.'

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


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password."""

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate(self, data: dict) -> dict:
        """Validates password fields."""

        user = self.context['request'].user
        if not user.check_password(data['current_password']):
            raise serializers.ValidationError(INCORRECT_CURRENT_PASSWORD)
        if data['new_password'] == data['current_password']:
            raise serializers.ValidationError(NEW_PASSWORD_IS_SAME)
        return data

    def update(self, instance: ApiUser, validated_data: dict) -> ApiUser:
        """Updates user password."""

        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance
