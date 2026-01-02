import json

from django.core.management.base import BaseCommand

from gastos.models import Brand


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for item in data:
                Brand.objects.create(**item)
        self.stdout.write(self.style.SUCCESS('Данные импортированы.'))
