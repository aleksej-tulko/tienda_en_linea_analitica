from re import findall, fullmatch

from rest_framework.validators import ValidationError

PROHIBITED_EMAIL_SYMBOLS = r'[^a-z0-9@._]'
PROHIBITED_EMAIL_STRUCTURE = r'^[a-z0-9]+[a-z0-9._]*@[a-z0-9]+\.[a-z]{2,}$'
INVALID_EMAIL_ERROR = 'Email contains prohibited symbols: {}.'
INVALID_EMAIL_STRUCTURE_ERROR = 'Enter a valid email.'


def regex_email(email):
    wrong_symbols = set(findall(PROHIBITED_EMAIL_SYMBOLS, email))
    if wrong_symbols:
        raise ValidationError(
            INVALID_EMAIL_ERROR.format(''.join(wrong_symbols))
        )
    if not fullmatch(PROHIBITED_EMAIL_STRUCTURE, email):
        raise ValidationError(INVALID_EMAIL_STRUCTURE_ERROR)
    return email
