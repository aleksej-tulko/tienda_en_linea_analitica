from django.contrib import admin

from gastos.models import (
    Brand,
    Category,
    Compra,
    Product,
    Tag
)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    list_editable = ('name',)
    list_filter = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    list_editable = ('name',)
    list_filter = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    list_editable = ('name',)
    list_filter = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        # 'titular',
        # 'name',
        'description',
        'price',
        'category',
        'brand',
        'ingressed_at',
    )
    # list_editable = ('name',)
    # list_filter = ('name',)
    # search_fields = ('name',)
    # ordering = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    list_editable = (
        'name',
        'slug',)
    list_filter = ('name',)
    search_fields = ('name',)
    ordering = ('id',)
