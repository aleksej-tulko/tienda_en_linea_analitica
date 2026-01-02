from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from gastos.constants import (
    MAX_PRICE,
    MIN_PRICE,
    NAME_LENGTH,
    TEXT_LENGHT
)


class AbstractNameModel(models.Model):

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Category(AbstractNameModel):

    name = models.CharField(
        blank=False,
        null=False,
        max_length=NAME_LENGTH,
        help_text='Up to 20 symbols',
        verbose_name='Category'
    )

    class Meta(AbstractNameModel.Meta):
        verbose_name_plural = 'Categories'


class Brand(AbstractNameModel):

    name = models.CharField(
        blank=False,
        null=False,
        max_length=NAME_LENGTH,
        help_text='Up to 20 symbols',
        verbose_name='Brand'
    )

    class Meta(AbstractNameModel.Meta):
        verbose_name_plural = 'Brands'


class Tag(AbstractNameModel):

    name = models.CharField(
        blank=False,
        null=False,
        max_length=NAME_LENGTH,
        unique=True,
        verbose_name='Tag')
    slug = models.SlugField(
        unique=True,
        verbose_name='Slug'
    )

    class Meta(AbstractNameModel.Meta):
        verbose_name_plural = 'Tags'


class Product(AbstractNameModel):

    name = models.CharField(
        max_length=NAME_LENGTH,
        unique=True,
        verbose_name='Product')

    class Meta(AbstractNameModel.Meta):
        verbose_name_plural = 'Products'


class Compra(models.Model):

    description = models.TextField(
        max_length=TEXT_LENGHT,
        null=False,
        blank=False,
        help_text='Up to 200 symbols',
        verbose_name='Description'
    )
    price = models.FloatField(
        null=False,
        blank=False,
        verbose_name='Price',
        help_text='Positive float value',
        validators=[MaxValueValidator(MAX_PRICE),
                    MinValueValidator(MIN_PRICE)]
    )
    category = models.ForeignKey(
        Category,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        verbose_name='Category'
    )
    brand = models.ForeignKey(
        Brand,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        verbose_name='Category'
    )
    products = models.ManyToManyField(
        Product,
        blank=False,
        through='CompraProduct',
        verbose_name='Goods'
    )
    tags = models.ManyToManyField(
        Tag,
        blank=False,
        verbose_name='Теги'
    )
    ingressed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created'
    )

    class Meta:
        default_related_name = 'compras'
        verbose_name_plural = 'Compras'
        ordering = ('-ingressed_at',)

    def __str__(self):
        return self.brand


class CompraProduct(models.Model):

    compra = models.ForeignKey(
        Compra,
        on_delete=models.CASCADE,
        verbose_name='Compra')
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Product')
    amount = models.FloatField(
        verbose_name='Amount',
        validators=[MinValueValidator(MIN_PRICE)]
    )

    class Meta:
        verbose_name_plural = 'Compra products'
        unique_together = ('compra', 'product',)

    def __str__(self):
        return (f'{self.amount} '
                f'{self.product.name} for {self.compra.name}'
                )
