from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from users.constants import (
    EMAIL_LENGTH,
    FIRST_NAME_LENGTH,
    LAST_NAME_LENGTH,
    PASSWORD_LENGTH,
    USERNAME_LENGTH,
    USERS_ORDER,
)


class ApiUser(AbstractUser):

    first_name = models.CharField(
        blank=False,
        null=False,
        max_length=FIRST_NAME_LENGTH,
        help_text='Up to 20 symbols',
        verbose_name='Name'
    )
    last_name = models.CharField(
        blank=False,
        null=False,
        max_length=LAST_NAME_LENGTH,
        help_text='Up to 20 symbols',
        verbose_name='Second name'
    )
    username = models.CharField(
        blank=False,
        null=False,
        max_length=USERNAME_LENGTH,
        unique=True,
        validators=[UnicodeUsernameValidator()],
        help_text='Up to 30 symbols',
        verbose_name='Nickname'
    )
    email = models.EmailField(
        blank=False,
        null=False,
        max_length=EMAIL_LENGTH,
        unique=True,
        help_text='Up to 40 symbols',
        verbose_name='Email',
    )
    password = models.CharField(
        blank=False,
        null=False,
        max_length=PASSWORD_LENGTH,
        help_text='Up to 200 symbols',
        verbose_name='Password'
    )

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'Users'
        ordering = USERS_ORDER

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('first_name', 'last_name', 'username',)

    def __str__(self):
        return self.username
