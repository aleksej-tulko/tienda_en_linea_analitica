from re import findall, fullmatch

from django.conf import settings
from rest_framework.validators import ValidationError

from api.constants import NOT_ALLOWED_SYMBOLS

INVALID_EMAIL_ERROR = 'Email contains prohibited symbols: {}.'
INVALID_EMAIL_STRUCTURE_ERROR = 'Enter a valid email.'
PROHIBITED_EMAIL_SYMBOLS = r'[^a-z0-9@._]'
PROHIBITED_EMAIL_STRUCTURE = r'^[a-z0-9]+[a-z0-9._]*@[a-z0-9]+\.[a-z]{2,}$'
PROHIBITED_USERNAME = 'Invalid username: {}.'
PROHIBITED_USERNAME_SYMBOLS = ('The username contains '
                               'prohibited symbols: {}')


def prohibited_usernames(username):
    if username in settings.PROHIBITED_NAMES:
        raise ValidationError(PROHIBITED_USERNAME.format(username))
    return username


def regex_username(username):
    wrong_symbols = set(findall(NOT_ALLOWED_SYMBOLS, username))
    if wrong_symbols:
        raise ValidationError(
            PROHIBITED_USERNAME_SYMBOLS.format(''.join(wrong_symbols))
        )
    return username


def regex_email(email):
    wrong_symbols = set(findall(PROHIBITED_EMAIL_SYMBOLS, email))
    if wrong_symbols:
        raise ValidationError(
            INVALID_EMAIL_ERROR.format(''.join(wrong_symbols))
        )
    if not fullmatch(PROHIBITED_EMAIL_STRUCTURE, email):
        raise ValidationError(INVALID_EMAIL_STRUCTURE_ERROR)
    return email
