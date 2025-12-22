# 🔐 How to Add Optimizer Admin Access

Есть 3 способа дать пользователю доступ к оптимизатору:

---

## Способ 1: Hardcoded список (текущий, самый быстрый)

**Файл:** `database.py`

```python
HARDCODED_OPTIMIZER_ADMINS = [
    '297936848',  # Main admin
    '123456789',  # Add new admin here
    '987654321',  # Another admin
]
```

**Плюсы:**
- ✅ Работает сразу, без перезапуска
- ✅ Не требует БД
- ✅ Быстро

**Минусы:**
- ❌ Нужно менять код
- ❌ Нужен git commit

**Применение:**
1. Отредактируйте `database.py`
2. Добавьте ID в список `HARDCODED_OPTIMIZER_ADMINS`
3. Если Docker: `docker restart backtester_web`

---

## Способ 2: Через SQL (рекомендуется для production)

### Вариант A: Если пользователь УЖЕ подписан на бота

```bash
docker exec -it backtester_postgres psql -U backtester -d backtester -c \
  "UPDATE market_data.bot_subscribers SET is_optimizer_admin = TRUE WHERE user_id = 123456789;"
```

### Вариант B: Если пользователя НЕТ в БД

```bash
docker exec -it backtester_postgres psql -U backtester -d backtester -c \
  "INSERT INTO market_data.bot_subscribers (user_id, username, is_optimizer_admin, active, notifications_enabled)
   VALUES (123456789, 'username', TRUE, TRUE, TRUE)
   ON CONFLICT (user_id) DO UPDATE SET is_optimizer_admin = TRUE;"
```

**Проверка:**
```bash
docker exec -it backtester_postgres psql -U backtester -d backtester -c \
  "SELECT user_id, username, is_optimizer_admin FROM market_data.bot_subscribers WHERE is_optimizer_admin = TRUE;"
```

**Плюсы:**
- ✅ Не требует изменения кода
- ✅ Постоянное хранение
- ✅ Можно управлять через admin panel

**Минусы:**
- ❌ Требует доступ к БД
- ❌ Нужна команда для каждого пользователя

---

## Способ 3: Через переменные окружения (TODO - не реализовано)

**Планируется в будущем:**

```bash
# В .env или docker-compose.yml
OPTIMIZER_ADMIN_IDS=297936848,123456789,987654321
```

Код будет читать из `os.getenv('OPTIMIZER_ADMIN_IDS')`.

**Плюсы:**
- ✅ Легко добавлять
- ✅ Не меняем код
- ✅ Хранится в конфиге

**Минусы:**
- ❌ Пока не реализовано (TODO)

---

## Способ 4: Admin Panel (TODO - не реализовано)

**Планируется:**

Web интерфейс: http://localhost:8000/admin/users

- Список всех пользователей
- Checkbox "Is Optimizer Admin"
- Кнопка "Save"

---

## Текущий статус:

**Работает сейчас:**
- ✅ Hardcoded список в `database.py`
- ✅ SQL через `UPDATE ... SET is_optimizer_admin = TRUE`

**ID вшит по умолчанию:**
- `297936848` (вы)

**TODO (будущие улучшения):**
1. Переменные окружения `OPTIMIZER_ADMIN_IDS`
2. Admin panel в Web UI
3. API endpoint для управления доступом
4. Role-based access control (admin, user, guest)

---

## Быстрая проверка доступа:

```bash
# Через API
curl "http://localhost:8000/api/optimize/queue"

# Через Python
docker exec -it backtester_web python -c "
from database import check_user_optimizer_access
print(check_user_optimizer_access('297936848'))  # Should print True
print(check_user_optimizer_access('999999999'))  # Should print False
"
```

---

## Как добавить СЕЙЧАС (пошагово):

### Для себя (вы):
✅ Уже добавлен (ID: 297936848)

### Для нового пользователя:

**1. Быстрый способ (hardcode):**
```bash
# Отредактируйте database.py
nano database.py

# Добавьте ID в список:
HARDCODED_OPTIMIZER_ADMINS = [
    '297936848',
    'NEW_USER_ID_HERE',  # <-- добавьте сюда
]

# Перезапустите
docker restart backtester_web
```

**2. Через SQL:**
```bash
docker exec -it backtester_postgres psql -U backtester -d backtester -c \
  "INSERT INTO market_data.bot_subscribers (user_id, is_optimizer_admin, active)
   VALUES ('NEW_USER_ID', TRUE, TRUE)
   ON CONFLICT (user_id) DO UPDATE SET is_optimizer_admin = TRUE;"
```

**3. Проверка:**
```bash
# Откройте http://localhost:8000/optimize
# Введите новый user_id
# Попробуйте запустить оптимизацию
```

Готово! 🎉
