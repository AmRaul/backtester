# Backup System - Quick Start

Краткая инструкция по работе с системой бэкапов Backtester.

## 🚀 Первичная настройка (один раз на проде)

```bash
# 1. SSH на сервер
ssh user@your-production-server

# 2. Перейти в директорию проекта
cd /opt/backtester

# 3. Настроить автоматические бэкапы (ежедневно в 3 AM)
./setup-backup-cron.sh

# 4. (Опционально) Настроить облачное хранилище
export BACKUP_S3_BUCKET="backtester-backups"
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"

# Или для Google Cloud
export BACKUP_GCS_BUCKET="backtester-backups"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"

# 5. (Опционально) Настроить Telegram уведомления
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"

# Добавить в .env чтобы сохранить
echo "BACKUP_S3_BUCKET=backtester-backups" >> .env
echo "TELEGRAM_BOT_TOKEN=your-token" >> .env
echo "TELEGRAM_CHAT_ID=your-chat-id" >> .env
```

✅ **Готово!** Теперь бэкапы создаются автоматически при каждом деплое и ежедневно.

---

## 📖 Частые операции

### Создать бэкап вручную

```bash
# Локально
./backup-db.sh local

# На проде
./backup-db.sh prod
```

### Посмотреть список бэкапов

```bash
ls -lh backups/

# Или с сортировкой по дате
ls -lht backups/ | head
```

### Восстановить из бэкапа

```bash
# Выбрать бэкап
ls -lh backups/backup_prod_*.sql.gz

# Восстановить (с подтверждением)
./restore-db.sh backups/backup_prod_20241221_030000.sql.gz prod
```

### Проверить статус бэкапов

```bash
./check-backups.sh prod

# Будет предупреждение если бэкап старше 24 часов
```

### Загрузить бэкап в облако

```bash
# AWS S3
./upload-backup-to-cloud.sh backups/backup_prod_20241221_030000.sql.gz s3

# Google Cloud Storage
./upload-backup-to-cloud.sh backups/backup_prod_20241221_030000.sql.gz gcs
```

### Скачать бэкап из облака

```bash
# AWS S3
aws s3 cp s3://backtester-backups/database-backups/backup_prod_20241221.sql.gz ./backups/

# Google Cloud
gsutil cp gs://backtester-backups/database-backups/backup_prod_20241221.sql.gz ./backups/
```

---

## 🆘 Аварийное восстановление

### Сценарий: "Миграция сломала базу"

```bash
# 1. Найти pre-deployment бэкап
ls -lht backups/pre_deploy_*.sql.gz | head -1

# 2. Восстановить
./restore-db.sh backups/pre_deploy_20241221_120000.sql.gz prod

# 3. Проверить
docker exec backtester_postgres_prod psql -U backtester -d backtester -c "SELECT COUNT(*) FROM backtester.backtest_history;"
```

### Сценарий: "База полностью потеряна"

```bash
# 1. Найти последний доступный бэкап
ls -lht backups/ | head -5

# 2. Если локальных нет - скачать из облака
aws s3 sync s3://backtester-backups/database-backups/ ./backups/

# 3. Восстановить самый свежий
LATEST=$(ls -t backups/backup_prod_*.sql.gz | head -1)
./restore-db.sh "$LATEST" prod

# 4. Проверить данные
docker exec backtester_postgres_prod psql -U backtester -d backtester -c "\dt backtester.*"
```

---

## 📅 Расписание бэкапов

### Текущее (после setup-backup-cron.sh):

- **3:00 AM каждый день** - автоматический бэкап продакшн БД
- **При каждом деплое** - pre-deployment бэкап (через CI/CD)

### Изменить время:

```bash
crontab -e

# Изменить строку (пример для 2 AM):
0 2 * * * cd /opt/backtester && ./backup-db.sh prod >> /var/log/backtester/backup.log 2>&1
```

### Добавить облачную загрузку:

```bash
crontab -e

# После бэкапа автоматом в облако:
5 3 * * * cd /opt/backtester && ./upload-backup-to-cloud.sh backups/backup_prod_$(date +\%Y\%m\%d)*.sql.gz s3 >> /var/log/backtester/backup.log 2>&1
```

---

## 📊 Мониторинг

### Посмотреть логи бэкапов

```bash
tail -f /var/log/backtester/backup.log
```

### Настроить автоматический мониторинг

```bash
crontab -e

# Проверять каждый час (Telegram алерт если проблема):
0 * * * * cd /opt/backtester && ./check-backups.sh prod >> /var/log/backtester/monitor.log 2>&1
```

---

## 📁 Структура бэкапов

```
/opt/backtester/backups/
├── pre_deploy_20241221_120000.sql.gz      # Деплой (хранится 7 дней)
├── pre_deploy_20241222_143000.sql.gz
├── backup_prod_20241221_030000.sql.gz     # Ежедневные (10 последних)
├── backup_prod_20241222_030000.sql.gz
└── ...

☁️ Облачное хранилище (опционально):
s3://backtester-backups/database-backups/   # AWS S3 (90 дней)
gs://backtester-backups/database-backups/   # Google Cloud (90 дней)
```

---

## ❓ Troubleshooting

### Бэкап не создается

```bash
# Проверить права
ls -l backup-db.sh
chmod +x backup-db.sh

# Запустить вручную с отладкой
./backup-db.sh prod 2>&1 | tee debug.log

# Проверить контейнер
docker ps | grep postgres
```

### Восстановление не работает

```bash
# Проверить файл
gunzip -t backups/backup_prod_YYYYMMDD.sql.gz

# Проверить место на диске
df -h

# Проверить контейнер
docker-compose -f docker-compose.prod.yml ps postgres
```

### Облачная загрузка не работает

```bash
# AWS
aws sts get-caller-identity
aws s3 ls s3://backtester-backups/

# Google Cloud
gcloud auth list
gsutil ls gs://backtester-backups/
```

---

## 📚 Полная документация

- **Автоматизация:** [BACKUP_AUTOMATION_GUIDE.md](BACKUP_AUTOMATION_GUIDE.md)
- **Миграции:** [DATABASE_MIGRATIONS_GUIDE.md](DATABASE_MIGRATIONS_GUIDE.md)
- **Сводка:** [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md)

---

## ✅ Checklist

**После настройки проверьте:**

- [ ] Cron job создан: `crontab -l`
- [ ] Тестовый бэкап успешен: `./backup-db.sh prod`
- [ ] Бэкапы в нужной папке: `ls -lh backups/`
- [ ] (Опционально) Облачная загрузка работает
- [ ] (Опционально) Telegram уведомления настроены
- [ ] Документ Emergency Recovery процедур доступен команде

**Готово!** 🎉
