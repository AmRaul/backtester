# Database Migrations Guide

Руководство по работе с миграциями базы данных PostgreSQL для Backtester.

## Система миграций

Backtester использует **простые SQL миграции** вместо сложных систем типа Alembic. Все миграции хранятся в папке `migrations/` и применяются автоматически при деплое через CI/CD.

### Преимущества

- ✅ Простота и прозрачность
- ✅ Версионирование через Git
- ✅ Автоматическое применение в CI/CD
- ✅ Идемпотентность (безопасное повторное применение)
- ✅ Откат через бэкапы

## Структура миграций

```
migrations/
├── README.md
├── 001_add_optimizer_tables.sql
├── 002_next_migration.sql
└── ...
```

### Правила именования

- **Формат:** `NNN_description.sql`
- **NNN** - трехзначный номер (001, 002, 003...)
- **description** - короткое описание на английском
- **Примеры:**
  - `001_add_optimizer_tables.sql`
  - `002_add_user_preferences.sql`
  - `003_add_performance_indexes.sql`

## Создание новой миграции

### Шаг 1: Создайте файл

```bash
# Найдите следующий номер
ls migrations/*.sql | tail -1
# Если последний 001, создаем 002

touch migrations/002_your_description.sql
```

### Шаг 2: Напишите SQL с идемпотентностью

**Всегда используйте:**
- `CREATE TABLE IF NOT EXISTS`
- `CREATE INDEX IF NOT EXISTS`
- `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`

**Пример миграции:**

```sql
-- Migration: Add user preferences
-- Created: 2024-12-21
-- Description: Add user_preferences table with notification settings

-- Create table
CREATE TABLE IF NOT EXISTS backtester.user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) UNIQUE NOT NULL,
    notification_email VARCHAR(255),
    theme VARCHAR(20) DEFAULT 'light',
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_prefs_user_id
ON backtester.user_preferences(user_id);

-- Add foreign key if needed
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_user_prefs_user'
    ) THEN
        ALTER TABLE backtester.user_preferences
        ADD CONSTRAINT fk_user_prefs_user
        FOREIGN KEY (user_id)
        REFERENCES market_data.bot_subscribers(user_id);
    END IF;
END $$;

-- Success message
SELECT 'Migration 002 completed: user_preferences table added' AS status;
```

### Шаг 3: Протестируйте локально

```bash
# Применить миграцию
docker exec -i backtester_postgres psql -U backtester -d backtester < migrations/002_your_description.sql

# Проверить результат
docker exec backtester_postgres psql -U backtester -d backtester -c "\dt backtester.*"

# Проверить идемпотентность (запустить повторно)
docker exec -i backtester_postgres psql -U backtester -d backtester < migrations/002_your_description.sql
```

### Шаг 4: Закоммитьте

```bash
git add migrations/002_your_description.sql
git commit -m "migration: add user preferences table"
git push
```

### Шаг 5: CI/CD применит автоматически

При деплое на продакшн CI/CD автоматически:
1. Скопирует все миграции на сервер
2. Применит все `*.sql` файлы по порядку
3. Пропустит уже примененные (благодаря `IF NOT EXISTS`)

## Применение миграций вручную

### Локально

```bash
# Одна миграция
docker exec -i backtester_postgres psql -U backtester -d backtester < migrations/001_add_optimizer_tables.sql

# Все миграции
for migration in migrations/*.sql; do
  echo "Applying $migration..."
  docker exec -i backtester_postgres psql -U backtester -d backtester < "$migration"
done
```

### На продакшне

```bash
# SSH на сервер
ssh user@your-server

cd /opt/backtester

# Одна миграция
docker exec -i backtester_postgres_prod psql -U backtester -d backtester < migrations/001_add_optimizer_tables.sql

# Все миграции
for migration in migrations/*.sql; do
  docker exec -i backtester_postgres_prod psql -U backtester -d backtester < "$migration"
done
```

## Бэкапы базы данных

### Создание бэкапа

```bash
# Локальная БД
./backup-db.sh local

# Продакшн БД
./backup-db.sh prod
```

**Что происходит:**
- Создается SQL дамп базы
- Сжимается в `.gz`
- Сохраняется в `backups/`
- Хранятся последние 10 бэкапов

### Восстановление из бэкапа

```bash
# Посмотреть доступные бэкапы
ls -lh backups/

# Восстановить локальную БД
./restore-db.sh backups/backup_local_20241221_153000.sql.gz local

# Восстановить продакшн БД
./restore-db.sh backups/backup_prod_20241221_153000.sql.gz prod
```

**⚠️ ВНИМАНИЕ:**
- Скрипт создаст safety backup перед восстановлением
- Требует подтверждения `yes`
- Полностью перезаписывает текущую БД

## Рекомендации

### Перед созданием миграции

1. **Сделайте бэкап:**
   ```bash
   ./backup-db.sh local
   ```

2. **Тестируйте локально** перед пушем в прод

3. **Проверьте идемпотентность** - запустите миграцию 2 раза

### Перед деплоем на прод

1. **Создайте бэкап прода:**
   ```bash
   ssh user@server "cd /opt/backtester && ./backup-db.sh prod"
   ```

2. **Проверьте CI/CD логи** после деплоя:
   ```
   📄 Applying migration: 001_add_optimizer_tables.sql
     ✅ 001_add_optimizer_tables.sql applied successfully
   ```

### Откат миграции

Откат делается через восстановление бэкапа:

```bash
# Найти бэкап перед миграцией
ls -lh backups/

# Восстановить
./restore-db.sh backups/backup_prod_YYYYMMDD_HHMMSS.sql.gz prod
```

## Частые проблемы

### Миграция не применилась

**Проверьте:**
1. Файл скопирован на сервер? (`ls /opt/backtester/migrations/`)
2. Postgres контейнер запущен? (`docker ps | grep postgres`)
3. Нет синтаксических ошибок в SQL?

**Решение:**
```bash
# Применить вручную с выводом ошибок
docker exec -i backtester_postgres_prod psql -U backtester -d backtester < migrations/XXX_migration.sql
```

### Ошибка "relation already exists"

**Причина:** Миграция уже применена

**Решение:** Это нормально! Благодаря `IF NOT EXISTS` миграция пропускается

### База повреждена после миграции

**Решение:**
```bash
# Восстановить последний бэкап
./restore-db.sh backups/backup_prod_latest.sql.gz prod
```

## Автоматизация

### Расписание бэкапов (cron)

```bash
# Добавить в crontab на сервере
crontab -e

# Бэкап каждый день в 3:00 AM
0 3 * * * cd /opt/backtester && ./backup-db.sh prod >> /var/log/backup.log 2>&1
```

### Pre-deployment бэкап в CI/CD

Добавить в `.github/workflows/ci-cd.yml` перед миграциями:

```yaml
# Создаем бэкап перед миграциями
echo "🔒 Creating pre-deployment backup..."
docker exec backtester_postgres_prod pg_dump -U ${{ secrets.DB_USER }} -d backtester | gzip > /opt/backtester/backups/pre_deploy_$(date +%Y%m%d_%H%M%S).sql.gz
```

## См. также

- `init-db.sql` - первичная инициализация БД
- `database.py` - SQLAlchemy модели
- `migrations/README.md` - краткая справка
