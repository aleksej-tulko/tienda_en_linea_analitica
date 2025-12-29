NOT_ALLOWED_SYMBOLS = r'[^\w.@+()\-\[\] ]'
USERS_FILTER = ('username',)
USERS_SEARCH = ('=username', '=email',)
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
    'avatar',
)
SUBSCRIPTION_FIELDS = (
    'avatar',
    'recipes',
    'following',
)
SHORT_LINK_URI = 'get-link'
SHORT_LINK_NAME = 'shortlink'
SUBSCRIBE_URI = 'subscribe'
SUBSCRIBE_NAME = 'subscribe'
SUBSCRIPTIONS_URI = 'subscriptions'
SUBSCRIPTIONS_NAME = 'subscriptions'
PASSWORD_URI = 'set_password'
PASSWORD_NAME = 'set_password'
PDF_URI = 'download_shopping_cart'
PDF_NAME = 'download_shopping_cart'
RECIPE_FIELDS = ('author',
                 'ingredients',
                 'tags',
                 'image',
                 'name',
                 'text',
                 'cooking_time',)
NESTED_RECIPE_FIELDS = ('id', 'name', 'image', 'cooking_time',)
