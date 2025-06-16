from django.core.management.base import BaseCommand
from recipes.models import ProductComponent
import json


class Command(BaseCommand):
    def handle(self, *args, **options):
        file_path = '/app/data/ingredients.json'

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

                ingredients = [
                    ProductComponent(
                        title=item['name'],
                        unit_type=item['measurement_unit']
                    )
                    for item in data
                ]

                ProductComponent.objects.bulk_create(ingredients, ignore_conflicts=True)

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Успешно импортировано {len(ingredients)} ингредиентов'
                    )
                )

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR('Файл ingredients.json не найден')
            )
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR('Ошибка: Некорректный формат JSON')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка: {str(e)}')
            )