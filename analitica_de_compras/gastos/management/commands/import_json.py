import json

from django.core.management.base import BaseCommand

from gastos.models import Brand, Category, Product, Tag


path_map = {
    Brand: 'data/brands.json',
    Category: 'data/categories.json',
    Product: 'data/products.json',
    Tag: 'data/tags.json'
}


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for model, data_path in path_map.items():
            with open(data_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for item in data:
                    model.objects.create(**item)
            self.stdout.write(self.style.SUCCESS('Данные импортированы.'))
