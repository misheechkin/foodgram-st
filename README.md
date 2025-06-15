# Foodgram — платформа для обмена рецептами

## Описание проекта
Foodgram — это веб-сервис, где пользователи могут делиться рецептами, подписываться на любимых авторов, добавлять рецепты в избранное

Проект построен на архитектуре REST API и упакован в Docker для удобства развертывания.

## Используемые технологии
- Python
- Django
- Django REST Framework
- PostgreSQL
- Nginx
- Docker
- GitHub Actions (CI/CD)

## Требования
- Docker
- Docker Compose

## 1. Клонирование репозитория
```bash
git clone https://github.com/misheechkin/foodgram-st
cd foodgram-st
```

## 2. Добавление .env
```bash
DATABASE_USER=
DATABASE_HOST=
DATABASE_NAME=
DATABASE_PASSWORD=
DATABASE_PORT=
ALLOWED_HOSTS=
SECRET_KEY=
```

## 3. Запуск проекта
### DEV VERSION
### Start front
1. ``npm install`` - Устанавливаем зависимости
2. ``npm run dev`` - Запускаем проект.
### Start back
1. ``pip install -r requirements.txt``
2. ``python manage.py migrate``
3. ``python manage.py runserver``

### PROD VERSION
``docker-compose up --build`` - запуск контейнеров

## 4. Загрузка данных в БД  

После запуска контейнеров выполните команду для загрузки тестовых данных (ингредиенты):

```bash
docker exec foodgram-backend python manage.py import_ingredients
```


## 5. Доступы и полезные ссылки
### После запуска проекта вы сможете воспользоваться следующими интерфейсами:

API документация (Swagger / Redoc)
Доступна по адресу:
```perl
http://<ваш_домен>/api/docs/ 
```

Здесь вы найдёте описание доступных эндпоинтов и сможете тестировать запросы напрямую в браузере.

Административная панель Django
Доступна по адресу:

```perl
http://<ваш_домен>/admin/ 
```

Для входа используйте учётные данные суперпользователя, которого нужно создать командой:

```bash
python manage.py createsuperuser
```


Сам сервер (главная страница фронтенда)
Главная страница доступна по адресу:

```perl
http://<ваш_домен>/      
```