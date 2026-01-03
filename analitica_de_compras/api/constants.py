POST_USER_FIELDS = (
    'id',
    'username',
    'email',
    'first_name',
    'last_name',
    'password',
)
GET_USER_FIELDS = (
    'id',
    'username',
    'email',
    'first_name',
    'last_name',
)
PASSWORD_URI = 'set_password'
PASSWORD_NAME = 'set_password'
INCORRECT_CURRENT_PASSWORD = 'Incorrect current password.'
NEW_PASSWORD_IS_SAME = 'The new password must not be the same as the old one.'
MIN_AMOUNT_ERROR = 'Amount cant be lesser than 1.'
PRODUCT_NON_EXISTING = 'No such good in database.'
NOT_ALLOWED_SYMBOLS = r'[^\w.@+()\-\[\] ]'
INVALID_EMAIL_ERROR = 'Email contains prohibited symbols: {}.'
INVALID_EMAIL_STRUCTURE_ERROR = 'Enter a valid email.'
PROHIBITED_EMAIL_SYMBOLS = r'[^a-z0-9@._]'
PROHIBITED_EMAIL_STRUCTURE = r'^[a-z0-9]+[a-z0-9._]*@[a-z0-9]+\.[a-z]{2,}$'
PROHIBITED_USERNAME = 'Invalid username: {}.'
PROHIBITED_USERNAME_SYMBOLS = (
    'The username contains '
    'prohibited symbols: {}'
)
