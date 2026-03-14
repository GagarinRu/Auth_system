# Система аутентификации и авторизации

[![Python](https://img.shields.io/badge/-Python-464646?style=flat-square&logo=Python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat-square&logo=Django)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat-square&logo=PostgreSQL)](https://www.postgresql.org/)

Собственная система разграничения прав доступа на основе JWT-токенов и ролевой модели (RBAC).

## Возможности

- ✅ Собственная система аутентификации (JWT, не Django Auth)
- ✅ Собственная система авторизации (RBAC с гибкими правами)
- ✅ Регистрация, вход, профиль, удаление аккаунта
- ✅ Управление ролями и правами (только для админа)
- ✅ Swagger документация
- ✅ Docker для быстрого запуска

## Быстрый старт

### Требования

- Docker
- Docker Compose

### Запуск через Docker Compose

```bash
# 1. Клонировать репозиторий
git clone <repo_url>
cd <repo_name>

# 2. Запустить контейнеры (файл .env уже есть в репозитории)
docker-compose up -d --build
```

### Переменные окружения

Основные переменные в `.env`:

```bash
# Django
SECRET_KEY=your_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=auth
POSTGRES_USER=postgres
POSTGRES_HOST=auth-db
POSTGRES_PORT=5432
POSTGRES_PASSWORD=your_password_here

# App
APP_GUVICORN_HOST=0.0.0.0
APP_GUVICORN_PORT=8000
```

### Доступные сервисы

| Сервис | URL |
|--------|-----|
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/api/v1/docs/ |
| PostgreSQL | localhost:5432 |

### Остановка

```bash
# Остановить контейнеры
docker-compose down

# Остановить и удалить данные
docker-compose down -v
```

### Первоначальная настройка

При первом запуске автоматически создаются:
- Миграции БД
- Роли: admin, user, manager
- Бизнес-объекты: documents, orders, products, roles
- Права доступа для каждой роли

## Архитектура системы доступа

### Схема данных (Mermaid)

```mermaid
erDiagram
    USER ||--o{ USER_ROLE : "1:N"
    USER_ROLE }o--|| ROLE : "N:1"
    ROLE ||--o{ ACCESS_ROLE_RULE : "1:N"
    ACCESS_ROLE_RULE }o--|| BUSINESS_ELEMENT : "N:1"

    USER {
        int id PK
        string email UK
        string first_name
        string last_name
        string password_hash
        boolean is_active
        datetime created_at
    }

    USER_ROLE {
        int id PK
        int user_id FK
        int role_id FK
        datetime assigned_at
    }

    ROLE {
        int id PK
        string name UK
        string description
    }

    ACCESS_ROLE_RULE {
        int id PK
        int role_id FK
        int element_id FK
        boolean read
        boolean read_all
        boolean can_create
        boolean update
        boolean update_all
        boolean delete
        boolean delete_all
    }

    BUSINESS_ELEMENT {
        int id PK
        string name UK
        string description
    }
```


### Архитектура потока запроса (Mermaid)

```mermaid
flowchart TD
    A["Request<br/>Authorization: Bearer token"] --> B["JWTAuthenticationMiddleware"]
    
    B --> C{"Token valid?"}
    C -->|No| D["401 Unauthorized"]
    C -->|Yes| E["request.user = User"]
    
    E --> F["has_access()"]
    F --> G["Get roles from UserRole"]
    G --> H["Find AccessRoleRule"]
    H --> I{"Has rights?"}
    
    I -->|No| J["403 Forbidden"]
    I -->|Yes| K["200 OK + data"]
    
    style D fill:#ffcccc
    style J fill:#ffcccc
    style K fill:#ccffcc
```

### Коды ответа

| Код | Описание |
|-----|----------|
| **200** | Успешный запрос |
| **201** | Создано |
| **400** | Ошибка валидации |
| **401** | Не аутентифицирован (нет токена) |
| **403** | Запрещено (нет прав) |
| **404** | Не найдено |

## Примеры использования API

### 1. Регистрация пользователя

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@test.com",
    "first_name": "Иван",
    "last_name": "Иванов",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'
```

**Ответ:**
```json
{
    "message": "Пользователь успешно зарегистрирован.",
    "user": {
        "id": 7,
        "email": "user@test.com",
        "first_name": "Иван",
        "last_name": "Иванов"
    }
}
```

### 2. Вход (получение токена)

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@test.com",
    "password": "SecurePass123!"
  }'
```

**Ответ:**
```json
{
    "message": "Успешный вход",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
        "id": 7,
        "email": "user@test.com",
        "first_name": "Иван",
        "last_name": "Иванов",
        "permissions": [
            {"element": "products", "read": true, "read_all": false, ...},
            {"element": "documents", "read": true, "read_all": false, ...},
            {"element": "orders", "read": true, "read_all": false, ...}
        ]
    }
}
```

### 3. Профиль пользователя

```bash
curl -X GET http://localhost:8000/api/v1/auth/profile/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Примеры для разных ролей

### Роль: USER (обычный пользователь)

По умолчанию новый пользователь получает роль `user`.

```bash
# Токен пользователя
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# ✅ Чтение своих документов
curl -X GET http://localhost:8000/api/v1/auth/documents/ \
  -H "Authorization: Bearer $TOKEN"
# Ответ: 200 [] (пусто, т.к. нет своих документов)

# ✅ Чтение товаров
curl -X GET http://localhost:8000/api/v1/auth/products/ \
  -H "Authorization: Bearer $TOKEN"
# Ответ: 200 [{"id":1,"name":"Ноутбук",...},...]

# ❌ Чтение всех документов (нужен read_all)
curl -X GET http://localhost:8000/api/v1/auth/documents/ \
  -H "Authorization: Bearer $TOKEN"
# Ответ: 200 [] (видит только свои)

# ❌ Доступ к управлению ролями
curl -X GET http://localhost:8000/api/v1/auth/roles/ \
  -H "Authorization: Bearer $TOKEN"
# Ответ: 403 {"error": "Доступ запрещён"}
```

### Роль: ADMIN (администратор)

Создадим админа и назначим роль:

```bash
# Регистрация админа
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "first_name": "Админ",
    "last_name": "Админов",
    "password": "Admin123!",
    "password_confirm": "Admin123!"
  }'

# Назначение роли admin (через БД или через API админа)
docker exec auth-db psql -U postgres -d auth -c "
  UPDATE user_roles SET role_id = (SELECT id FROM roles WHERE name='admin')
  WHERE user_id = (SELECT id FROM users WHERE email='admin@test.com');
"

# Логин как админ
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "Admin123!"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# ✅ Чтение всех документов (read_all=True)
curl -X GET http://localhost:8000/api/v1/auth/documents/ \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# Ответ: 200 [{"id":1,"title":"Договор...","owner_id":1,...},...]

# ✅ Управление ролями
curl -X GET http://localhost:8000/api/v1/auth/roles/ \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# Ответ: 200 [{"id":4,"name":"admin",...},...]

# ✅ Создание роли
curl -X POST http://localhost:8000/api/v1/auth/roles/create/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "moderator",
    "description": "Модератор",
    "elements": [
      {"element": "documents", "read": true, "read_all": true, "can_create": true}
    ]
  }'
```

### Роль: MANAGER (менеджер)

```bash
# Назначение роли manager
docker exec auth-db psql -U postgres -d auth -c "
  INSERT INTO user_roles (user_id, role_id)
  SELECT u.id, r.id FROM users u, roles r
  WHERE u.email = 'user@test.com' AND r.name = 'manager'
  ON CONFLICT (user_id, role_id) DO NOTHING;
"

# ✅ Полный доступ к заказам
curl -X GET http://localhost:8000/api/v1/auth/orders/ \
  -H "Authorization: Bearer $TOKEN"
# Ответ: 200 [{"id":1,"description":"Заказ №1",...},...]

# ✅ Чтение товаров
curl -X GET http://localhost:8000/api/v1/auth/products/ \
  -H "Authorization: Bearer $TOKEN"
# Ответ: 200 [{"id":1,"name":"Ноутбук",...},...]
```

---

## Матрица прав доступа

| Роль | documents | orders | products | roles |
|------|:---------:|:------:|:--------:|:-----:|
| **admin** | Полный | Полный | Полный | Полный |
| **manager** | — | Полный | Свои | — |
| **user** | Свои | Свои | Свои | — |

**Обозначения:**
- **Полный** = read + read_all + create + update + update_all + delete + delete_all
- **Свои** = только чтение своих объектов (где owner_id = user.id)

---

## API Endpoints

### Аутентификация

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/v1/auth/register/` | Регистрация |
| POST | `/api/v1/auth/login/` | Вход |
| POST | `/api/v1/auth/logout/` | Выход |
| GET | `/api/v1/auth/profile/` | Профиль |
| PUT | `/api/v1/auth/profile/` | Обновить профиль |
| DELETE | `/api/v1/auth/delete-account/` | Удалить аккаунт |

### Управление доступом (admin)

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/v1/auth/roles/` | Список ролей |
| POST | `/api/v1/auth/roles/create/` | Создать роль |
| PUT | `/api/v1/auth/roles/<id>/update/` | Обновить роль |
| POST | `/api/v1/auth/user-role/assign/` | Назначить роль |
| POST | `/api/v1/auth/user-role/remove/` | Удалить роль |
| GET | `/api/v1/auth/business-element/` | Бизнес-объекты |

### Бизнес-объекты (mock)

| Метод | URL | Описание |
|-------|-----|----------|
| GET/POST | `/api/v1/auth/documents/` | Документы |
| GET/PUT/DELETE | `/api/v1/auth/documents/<id>/` | Документ |
| GET | `/api/v1/auth/orders/` | Заказы |
| GET | `/api/v1/auth/products/` | Товары |

---

## Управление через БД

### Просмотр ролей

```bash
docker exec auth-db psql -U postgres -d auth -c "SELECT * FROM roles;"
```

### Просмотр прав

```bash
docker exec auth-db psql -U postgres -d auth -c "
  SELECT r.name as role, e.name as element, read, read_all, can_create
  FROM access_role_rules arr
  JOIN roles r ON r.id = arr.role_id
  JOIN business_elements e ON e.id = arr.element_id;
"
```

### Назначение роли

```bash
docker exec auth-db psql -U postgres -d auth -c "
  INSERT INTO user_roles (user_id, role_id)
  SELECT (SELECT id FROM users WHERE email='user@test.com'),
         (SELECT id FROM roles WHERE name='admin')
  ON CONFLICT (user_id, role_id) DO NOTHING;
"
```

---

## Разработка

### Структура проекта

```
app/
├── src/
│   ├── auth_app/
│   │   ├── management/commands/init_rbac.py  # Инициализация прав
│   │   ├── migrations/                        # Миграции
│   │   ├── models.py                          # Модели
│   │   ├── views.py                           # Views
│   │   ├── serializers.py                     # Serializers
│   │   ├── permissions.py                     # Декораторы прав
│   │   ├── middleware.py                      # JWT аутентификация
│   │   └── urls.py                            # URL роутинг
│   ├── config/
│   │   ├── settings.py                        # Настройки
│   │   └── urls.py                            # Главные URL
│   └── manage.py
├── entrypoint.sh                              # Точка входа
├── Dockerfile
└── docker-compose.yml
```

### Команды Docker Compose

```bash
# Пересобрать и запустить
docker-compose up -d --build

# Остановить
docker-compose stop

# Перезапустить
docker-compose restart

# Логи
docker-compose logs -f api
docker-compose logs -f db

# Выполнить команду внутри контейнера
docker-compose exec api python manage.py migrate
docker-compose exec api python manage.py createsuperuser

# Подключиться к БД
docker-compose exec db psql -U postgres -d auth
```

---

## Автор

Evgeny Kudryashov: https://github.com/GagarinRu
