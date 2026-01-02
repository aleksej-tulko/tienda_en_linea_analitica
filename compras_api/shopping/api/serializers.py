from typing import List

from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.constants import (
    INCORRECT_CURRENT_PASSWORD,
    GET_USER_FIELDS,
    PRODUCT_NON_EXISTING,
    MIN_AMOUNT_ERROR,
    NEW_PASSWORD_IS_SAME,
    POST_USER_FIELDS,
)
from api.validators import prohibited_usernames, regex_username
from users.models import ApiUser
from gastos.models import (
    Brand,
    Category,
    Compra,
    CompraProduct,
    Product,
    Tag
)

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


class BrandSerializer(serializers.ModelSerializer):

    class Meta:
        model = Brand
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class CompraResponseSerializer(serializers.ModelSerializer):
    """Serializer for displaying recipes."""

    titular = ReadUserSerializer(read_only=True)
    products = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    def get_products(self, obj: Compra) -> List[dict]:
        """Returns a list of ingredients for the recipe."""

        products = CompraProduct.objects.filter(compra=obj)

        return [
            {
                'id': item.product.id,
                'name': item.product.name,
                'amount': item.amount,
            } for item in products]

    def get_tags(self, obj: Compra) -> List[dict]:
        """Returns a list of tags for the recipe."""

        return TagSerializer(obj.tags.all(), many=True).data

    class Meta:
        model = Compra
        fields = '__all__'


class CompraProductsCreateSerializer(serializers.Serializer):
    """Serializer for displaying recipe ingredients."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product',
        error_messages={'does_not_exist':
                        PRODUCT_NON_EXISTING.format('{pk_value}')})
    amount = serializers.IntegerField(
        min_value=1, error_messages={'min_value': MIN_AMOUNT_ERROR}
    )


class CompraSerializer(serializers.ModelSerializer):

    titular = ReadUserSerializer(read_only=True)
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    price = serializers.FloatField(required=True)
    brand = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all()
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all()
    )
    products = CompraProductsCreateSerializer(many=True, write_only=True)
    tags = serializers.ListField(
        child=serializers.SlugRelatedField(
            queryset=Tag.objects.all(),
            slug_field='slug',
            write_only=True
        )
    )

    class Meta:
        model = Compra
        fields = (
            'titular',
            'name',
            'description',
            'price',
            'brand',
            'category',
            'products',
            'tags',
        )

    def create(self, validated_data: dict) -> Compra:
        """Creates and saves a new recipe."""

        products_data = validated_data.pop('products')
        tags_data = validated_data.pop('tags')
        validated_data['titular'] = self.context['request'].user
        compra = Compra.objects.create(**validated_data)
        self._create_products(products_data, compra)
        compra.tags.set(tags_data)
        return compra

    def to_representation(self, instance: Compra) -> dict:
        """Returns the serialized representation of the recipe."""

        return CompraResponseSerializer(
            instance, context={'request': self.context.get('request')}
        ).data

    @staticmethod
    def _create_products(
        products_data: List[dict],
        compra: Compra
    ) -> None:
        """Creates and associates ingredients with a recipe."""
        compra_products = [
            CompraProduct(
                compra=compra,
                product=product_data['product'],
                amount=product_data['amount']
            )
            for product_data in products_data
        ]
        CompraProduct.objects.bulk_create(compra_products)
