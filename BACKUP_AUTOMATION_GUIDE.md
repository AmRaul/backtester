# Backup Automation Guide

Полное руководство по автоматизации бэкапов базы данных PostgreSQL для Backtester.

## 📋 Содержание

1. [Обзор системы бэкапов](#обзор-системы-бэкапов)
2. [Автоматические бэкапы](#автоматические-бэкапы)
3. [Облачное хранилище](#облачное-хранилище)
4. [Мониторинг бэкапов](#мониторинг-бэкапов)
5. [Восстановление данных](#восстановление-данных)
6. [Emergency Recovery](#emergency-recovery)

---

## Обзор системы бэкапов

### 🎯 Когда создаются бэкапы?

#### 1. **При каждом деплое (автоматически)**
   - Срабатывает в CI/CD перед применением миграций
   - Сохраняется как `pre_deploy_YYYYMMDD_HHMMSS.sql.gz`
   - Хранится 7 дней
   - Локация: `/opt/backtester/backups/` на сервере

#### 2. **Ежедневно в 3:00 AM (cron)**
   - Регулярный бэкап продакшн базы
   - Сохраняется как `backup_prod_YYYYMMDD_HHMMSS.sql.gz`
   - Хранится 10 последних версий
   - Опционально загружается в облако (S3/GCS)

#### 3. **Вручную (по требованию)**
   ```bash
   ./backup-db.sh prod    # Продакшн
   ./backup-db.sh local   # Локальная БД
   ```

### 📁 Где хранятся бэкапы?

```
/opt/backtester/backups/
├── pre_deploy_20241221_120000.sql.gz     # Деплой бэкапы
├── pre_deploy_20241222_143000.sql.gz
├── backup_prod_20241221_030000.sql.gz    # Ежедневные бэкапы
├── backup_prod_20241222_030000.sql.gz
└── ...
```

**Облачное хранилище (опционально):**
- AWS S3: `s3://your-bucket/database-backups/`
- Google Cloud Storage: `gs://your-bucket/database-backups/`

---

## Автоматические бэкапы

### Настройка на сервере

#### Шаг 1: Установка автоматических бэкапов

```bash
# SSH на продакшн сервер
ssh user@your-server

cd /opt/backtester

# Запустить установку cron
sudo ./setup-backup-cron.sh
```

**Что это делает:**
- ✅ Создает cron job для ежедневных бэкапов в 3:00 AM
- ✅ Настраивает logrotate для логов (хранит 30 дней)
- ✅ Делает тестовый бэкап
- ✅ Показывает текущее расписание

#### Шаг 2: Проверка настройки

```bash
# Посмотреть cron jobs
crontab -l

# Проверить логи бэкапов
tail -f /var/log/backtester/backup.log

# Список бэкапов
ls -lh /opt/backtester/backups/
```

### Изменение расписания

Чтобы изменить время бэкапа:

```bash
# Открыть crontab
crontab -e

# Изменить строку (пример: каждый день в 2:00 AM)
0 2 * * * cd /opt/backtester && ./backup-db.sh prod >> /var/log/backtester/backup.log 2>&1
```

**Примеры расписаний:**
```bash
0 3 * * *     # Каждый день в 3:00
0 */6 * * *   # Каждые 6 часов
0 2 * * 0     # Каждое воскресенье в 2:00
0 0 1 * *     # 1-го числа каждого месяца
```

---

## Облачное хранилище

### AWS S3 Setup

#### 1. Создать S3 bucket

```bash
aws s3 mb s3://backtester-backups --region us-east-1
```

#### 2. Настроить переменные окружения

```bash
# Добавить в ~/.bashrc или /opt/backtester/.env
export BACKUP_S3_BUCKET="backtester-backups"
export AWS_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
```

#### 3. Загрузить бэкап в S3

```bash
# Вручную
./upload-backup-to-cloud.sh backups/backup_prod_20241221_030000.sql.gz s3

# Автоматически после бэкапа (добавить в cron)
0 3 * * * cd /opt/backtester && ./backup-db.sh prod && ./upload-backup-to-cloud.sh backups/backup_prod_$(date +\%Y\%m\%d)*.sql.gz s3 >> /var/log/backtester/backup.log 2>&1
```

#### 4. Восстановить из S3

```bash
# Скачать последний бэкап
aws s3 cp s3://backtester-backups/database-backups/backup_prod_YYYYMMDD_HHMMSS.sql.gz ./

# Восстановить
./restore-db.sh backup_prod_YYYYMMDD_HHMMSS.sql.gz prod
```

### Google Cloud Storage Setup

#### 1. Создать GCS bucket

```bash
gsutil mb -c NEARLINE -l us-east1 gs://backtester-backups
```

#### 2. Настроить переменные окружения

```bash
export BACKUP_GCS_BUCKET="backtester-backups"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

#### 3. Загрузить в GCS

```bash
./upload-backup-to-cloud.sh backups/backup_prod_20241221_030000.sql.gz gcs
```

#### 4. Восстановить из GCS

```bash
# Скачать
gsutil cp gs://backtester-backups/database-backups/backup_prod_YYYYMMDD_HHMMSS.sql.gz ./

# Восстановить
./restore-db.sh backup_prod_YYYYMMDD_HHMMSS.sql.gz prod
```

---

## Мониторинг бэкапов

### Проверка статуса бэкапов

```bash
# Проверить локальные бэкапы
./check-backups.sh prod

# Вывод:
# 🔍 Checking backup status...
# 📊 Latest Backup:
#    File: backup_prod_20241221_030000.sql.gz
#    Size: 52M
#    Date: 2024-12-21 03:00:15
#    Age: 12h 30m
# ✅ Status: OK
```

### Настройка Telegram уведомлений

#### 1. Получить Bot Token и Chat ID

```bash
# 1. Создать бота через @BotFather в Telegram
# 2. Получить chat_id через @userinfobot
```

#### 2. Настроить переменные

```bash
# Добавить в ~/.bashrc или /opt/backtester/.env
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

#### 3. Добавить мониторинг в cron

```bash
crontab -e

# Проверять каждый час (алерт если бэкап старше 24h)
0 * * * * cd /opt/backtester && ./check-backups.sh prod >> /var/log/backtester/monitor.log 2>&1
```

**Что будет:**
- ✅ Если бэкап свежий (< 24h) - только логи, без уведомлений
- ⚠️ Если бэкап старый (> 24h) - отправит Telegram сообщение
- ❌ Если бэкапов нет вообще - критический алерт

---

## Восстановление данных

### Сценарий 1: Откат после неудачной миграции

```bash
# 1. Найти pre-deployment бэкап
ls -lh /opt/backtester/backups/pre_deploy_*.sql.gz

# 2. Восстановить
./restore-db.sh backups/pre_deploy_20241221_120000.sql.gz prod

# 3. Проверить
docker exec backtester_postgres_prod psql -U backtester -d backtester -c "\dt backtester.*"
```

### Сценарий 2: Восстановление к определенной дате

```bash
# 1. Посмотреть доступные бэкапы
ls -lh backups/backup_prod_*.sql.gz

# 2. Выбрать нужную дату
./restore-db.sh backups/backup_prod_20241215_030000.sql.gz prod

# 3. Проверить данные
docker exec backtester_postgres_prod psql -U backtester -d backtester -c "SELECT COUNT(*) FROM backtester.backtest_history;"
```

### Сценарий 3: Восстановление из облака

```bash
# AWS S3
aws s3 ls s3://backtester-backups/database-backups/
aws s3 cp s3://backtester-backups/database-backups/backup_prod_YYYYMMDD.sql.gz ./backups/

# Google Cloud
gsutil ls gs://backtester-backups/database-backups/
gsutil cp gs://backtester-backups/database-backups/backup_prod_YYYYMMDD.sql.gz ./backups/

# Восстановить
./restore-db.sh backups/backup_prod_YYYYMMDD.sql.gz prod
```

### Сценарий 4: Копирование прод данных на локальный dev

```bash
# 1. На сервере - создать бэкап
ssh user@server "cd /opt/backtester && ./backup-db.sh prod"

# 2. Скачать на локальную машину
scp user@server:/opt/backtester/backups/backup_prod_$(date +%Y%m%d)_*.sql.gz ./backups/

# 3. Восстановить локально
./restore-db.sh backups/backup_prod_YYYYMMDD_HHMMSS.sql.gz local
```

---

## Emergency Recovery

### 🚨 Полная потеря базы данных

#### 1. Восстановление из последнего бэкапа

```bash
# Проверить Docker контейнеры
docker ps -a | grep postgres

# Если контейнер не запущен
docker-compose -f docker-compose.prod.yml up -d postgres

# Подождать готовности
sleep 10

# Найти последний бэкап
LATEST_BACKUP=$(ls -t backups/backup_prod_*.sql.gz | head -1)
echo "Restoring from: $LATEST_BACKUP"

# Восстановить (скрипт создаст safety backup автоматически)
./restore-db.sh "$LATEST_BACKUP" prod

# Проверить целостность
docker exec backtester_postgres_prod psql -U backtester -d backtester -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname IN ('backtester', 'market_data')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

#### 2. Восстановление из облака (если локальные бэкапы потеряны)

```bash
# AWS S3
aws s3 sync s3://backtester-backups/database-backups/ ./backups/

# Или Google Cloud
gsutil -m rsync gs://backtester-backups/database-backups/ ./backups/

# Найти последний
LATEST_BACKUP=$(ls -t backups/backup_prod_*.sql.gz | head -1)

# Восстановить
./restore-db.sh "$LATEST_BACKUP" prod
```

#### 3. Восстановление с минимальной потерей данных

```bash
# 1. Проверить все источники бэкапов
echo "=== Local backups ==="
ls -lh backups/backup_prod_*.sql.gz | tail -5

echo "=== Pre-deployment backups ==="
ls -lh backups/pre_deploy_*.sql.gz | tail -3

echo "=== Cloud backups (S3) ==="
aws s3 ls s3://backtester-backups/database-backups/ | tail -5

# 2. Выбрать самый свежий
# 3. Восстановить
# 4. Проверить потерю данных

docker exec backtester_postgres_prod psql -U backtester -d backtester -c "
SELECT
    'backtest_history' AS table_name,
    COUNT(*) AS records,
    MAX(created_at) AS latest_record
FROM backtester.backtest_history
UNION ALL
SELECT
    'optimization_results',
    COUNT(*),
    MAX(created_at)
FROM backtester.optimization_results;
"
```

### 📞 Контакты для экстренных случаев

**Расположение credentials:**
- AWS credentials: `~/.aws/credentials` или в GitHub Secrets
- GCS credentials: `/path/to/service-account-key.json`
- Database credentials: `/opt/backtester/.env`

**Проверка доступа:**
```bash
# AWS
aws sts get-caller-identity

# Google Cloud
gcloud auth list

# Database
docker exec backtester_postgres_prod psql -U backtester -d backtester -c "SELECT version();"
```

---

## Checklist для Production

### ✅ Initial Setup

- [ ] Установлен cron для ежедневных бэкапов
- [ ] Настроен logrotate для логов
- [ ] Протестирован backup-db.sh
- [ ] Протестирован restore-db.sh
- [ ] Создан S3/GCS bucket
- [ ] Настроены credentials для облака
- [ ] Протестирована загрузка в облако
- [ ] Настроены Telegram уведомления
- [ ] Протестирован check-backups.sh
- [ ] Документированы процедуры восстановления

### ✅ Weekly Verification

- [ ] Проверить наличие свежих бэкапов
- [ ] Проверить размер бэкапов (должен быть стабильным)
- [ ] Проверить логи бэкапов на ошибки
- [ ] Проверить облачные бэкапы
- [ ] Протестировать восстановление (на dev окружении)

### ✅ Monthly Drill

- [ ] Восстановить базу из бэкапа на тестовом сервере
- [ ] Проверить целостность данных
- [ ] Засечь время восстановления
- [ ] Обновить документацию если нужно

---

## Troubleshooting

### Бэкап не создается

**Проверить:**
```bash
# Cron работает?
service cron status

# Права доступа
ls -l backup-db.sh
chmod +x backup-db.sh

# Postgres контейнер запущен?
docker ps | grep postgres

# Ручной запуск с отладкой
./backup-db.sh prod 2>&1 | tee backup-debug.log
```

### Восстановление не работает

**Проверить:**
```bash
# Файл существует и не поврежден?
gunzip -t backups/backup_prod_YYYYMMDD.sql.gz

# Достаточно места?
df -h /var/lib/docker

# Postgres запущен?
docker-compose -f docker-compose.prod.yml ps postgres
```

### Облачная загрузка не работает

**AWS S3:**
```bash
# Проверить credentials
aws sts get-caller-identity

# Проверить bucket
aws s3 ls s3://backtester-backups/

# Права доступа
aws s3api get-bucket-acl --bucket backtester-backups
```

**Google Cloud:**
```bash
# Проверить auth
gcloud auth list

# Проверить bucket
gsutil ls gs://backtester-backups/

# Права доступа
gsutil iam get gs://backtester-backups/
```

---

## Итог

Теперь у вас есть **полностью автоматизированная система бэкапов**:

✅ **Автоматические бэкапы:**
- При каждом деплое (pre-deployment)
- Ежедневно в 3 AM (cron)
- Вручную когда нужно

✅ **Облачное хранилище:**
- AWS S3 с lifecycle policy (90 дней)
- Google Cloud Storage с автоудалением
- Versioning для защиты от случайного удаления

✅ **Мониторинг:**
- Автоматическая проверка возраста бэкапов
- Telegram алерты при проблемах
- Логирование всех операций

✅ **Восстановление:**
- Простые скрипты для любого сценария
- Safety backup перед восстановлением
- Документированные процедуры

**Следующий шаг:** Запустить `./setup-backup-cron.sh` на продакшн сервере! 🚀
