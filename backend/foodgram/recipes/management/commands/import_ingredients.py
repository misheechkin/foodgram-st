import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from recipes.models import ProductComponent


class Command(BaseCommand):
    help = _('Импорт продуктов из JSON файла')

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/ingredients.json',
            help=_('Путь к JSON файлу с продуктами (относительно корня проекта)')
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help=_('Очистить таблицу продуктов перед импортом')
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        # Формируем полный путь к файлу
        if not os.path.isabs(file_path):
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(settings.BASE_DIR)))
            full_path = os.path.join(project_root, file_path)
        else:
            full_path = file_path
            
        if not os.path.exists(full_path):
            raise CommandError(_('Файл %(file_path)s не найден') % {'file_path': full_path})

        # Очищаем таблицу если нужно
        if options['clear']:
            ProductComponent.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(_('Таблица продуктов очищена'))
            )

        try:
            with open(full_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise CommandError(_('Ошибка чтения JSON файла: %(error)s') % {'error': str(e)})

        if not isinstance(data, list):
            raise CommandError(_('JSON файл должен содержать массив объектов'))

        created_count = 0
        updated_count = 0
        
        for item in data:
            if not isinstance(item, dict):
                self.stdout.write(
                    self.style.WARNING(_('Пропущен некорректный элемент: %(item)s') % {'item': item})
                )
                continue
                
            # Проверяем обязательные поля
            if 'name' not in item or 'measurement_unit' not in item:
                self.stdout.write(
                    self.style.WARNING(
                        _('Пропущен элемент без обязательных полей name/measurement_unit: %(item)s') % {'item': item}
                    )
                )
                continue

            title = item['name'].strip()
            unit_type = item['measurement_unit'].strip()
            
            if not title or not unit_type:
                self.stdout.write(
                    self.style.WARNING(
                        _('Пропущен элемент с пустыми полями: %(item)s') % {'item': item}
                    )
                )
                continue

            # Создаем или обновляем продукт
            product, created = ProductComponent.objects.get_or_create(
                title=title,
                defaults={'unit_type': unit_type}
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        _('Создан продукт: %(title)s (%(unit)s)') % {
                            'title': product.title, 
                            'unit': product.unit_type
                        }
                    )
                )
            else:
                # Обновляем единицу измерения если она отличается
                if product.unit_type != unit_type:
                    product.unit_type = unit_type
                    product.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            _('Обновлен продукт: %(title)s (%(unit)s)') % {
                                'title': product.title, 
                                'unit': product.unit_type
                            }
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                _('Импорт завершен. Создано: %(created)d, обновлено: %(updated)d продуктов') % {
                    'created': created_count,
                    'updated': updated_count
                }
            )
        )
