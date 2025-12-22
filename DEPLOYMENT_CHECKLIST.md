# 🚀 Deployment Checklist - Strategy Optimizer

После push на сервер выполните эти шаги:

---

## ✅ Pre-deployment (на локальной машине)

### 1. Проверьте что все файлы добавлены в git

```bash
git status

# Должны быть добавлены:
# - optimizer.py
# - optimization_queue.py
# - optimization_config_*.json (3 файла)
# - templates/optimize.html
# - templates/optimization_results.html
# - database.py (обновлен)
# - init-db.sql (обновлен)
# - web_app.py (обновлен)
# - main.py (обновлен)
# - requirements.txt (обновлен)
# - market-analytics/bot/notifications.py (обновлен)
# - market-analytics/requirements.txt (обновлен)
# - docker-compose.yml (обновлен)
# - .env.example (обновлен)
# - README_OPTIMIZER.md
# - DOCKER_OPTIMIZATION_GUIDE.md
# - OPTIMIZATION_QUICKSTART.md
# - HOW_TO_ADD_OPTIMIZER_ADMIN.md
# - RUN_OPTIMIZATION.sh
```

### 2. Закоммитьте изменения

```bash
git add .
git commit -m "feat: add strategy optimizer with Optuna

- Bayesian optimization for strategy parameters
- Support for indicators (RSI, EMA) and DCA-only optimization
- Queue system (max 1 concurrent optimization)
- Telegram notifications for progress
- Web UI + CLI + API interfaces
- Hardcoded admin ID: 297936848
- Docker ready"

git push origin main
```

---

## 🔧 Deployment на сервере

### 1. Pull изменений

```bash
cd /path/to/backtester
git pull origin main
```

### 2. Обновите .env файл (если нужно)

```bash
nano .env

# Проверьте что есть:
TELEGRAM_BOT_TOKEN=your_token
DB_USER=backtester
DB_PASSWORD=your_password
# ... остальные переменные
```

### 3. Остановите контейнеры

```bash
docker-compose down
```

### 4. Пересоберите образы (ВАЖНО!)

```bash
# Пересборка с новыми зависимостями (optuna, python-telegram-bot)
docker-compose build --no-cache backtester-web
docker-compose build --no-cache telegram-bot

# Или все сразу:
docker-compose build --no-cache
```

### 5. Примените миграции БД

**Вариант A: Если БД уже существует (UPDATE)**

```bash
# Запустите только postgres
docker-compose up -d postgres

# Подождите пока стартует
sleep 5

# Добавьте новые таблицы
docker exec -i backtester_postgres psql -U backtester -d backtester << 'EOF'
-- Optimization results table
CREATE TABLE IF NOT EXISTS backtester.optimization_results (
    id SERIAL PRIMARY KEY,
    task_id UUID UNIQUE NOT NULL,
    symbol VARCHAR(50),
    timeframe VARCHAR(10),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    n_trials INTEGER DEFAULT 100,
    optimization_metric VARCHAR(50) DEFAULT 'custom_score',
    best_params JSONB,
    best_score NUMERIC(12,4),
    best_config JSONB,
    best_results JSONB,
    all_trials JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_minutes NUMERIC(10,2),
    user_id VARCHAR(100)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_optimization_task_id ON backtester.optimization_results(task_id);
CREATE INDEX IF NOT EXISTS idx_optimization_created ON backtester.optimization_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_optimization_status ON backtester.optimization_results(status);
CREATE INDEX IF NOT EXISTS idx_optimization_user ON backtester.optimization_results(user_id);
CREATE INDEX IF NOT EXISTS idx_optimization_best_params ON backtester.optimization_results USING GIN (best_params);
CREATE INDEX IF NOT EXISTS idx_optimization_all_trials ON backtester.optimization_results USING GIN (all_trials);

-- Add optimizer admin flag to bot_subscribers
ALTER TABLE market_data.bot_subscribers
ADD COLUMN IF NOT EXISTS is_optimizer_admin BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_subscribers_optimizer_admin
ON market_data.bot_subscribers(is_optimizer_admin)
WHERE is_optimizer_admin = TRUE;

-- Success message
SELECT 'Optimization tables created successfully!' as status;
EOF

echo "✅ Database migration completed"
```

**Вариант B: Если БД новая (будет автоматически через init-db.sql)**

Если вы разворачиваете с нуля, таблицы создадутся автоматически из `init-db.sql`.

### 6. Запустите все сервисы

```bash
docker-compose up -d

# Проверьте логи
docker-compose logs -f backtester-web | head -50
docker-compose logs -f telegram-bot | head -50
```

### 7. Проверьте что всё работает

```bash
# Health check
curl http://localhost:8000/health

# Queue status
curl http://localhost:8000/api/optimize/queue

# Web UI
curl -I http://localhost:8000/optimize

# Check logs for errors
docker logs backtester_web 2>&1 | grep -i error | tail -20
```

---

## 🧪 Тестирование после deployment

### 1. Проверьте Web UI

Откройте в браузере:
```
http://YOUR_SERVER_IP:8000/optimize
```

Должны видеть форму с вашим ID `297936848` уже подставленным.

### 2. Запустите тестовую оптимизацию (небольшую)

```bash
docker exec -it backtester_web python main.py \
  --optimize \
  --optimization-config optimization_config_no_indicators.json \
  --user-id 297936848 \
  --n-trials 10
```

Это займёт ~2-3 минуты. Вы должны получить Telegram уведомления.

### 3. Проверьте БД

```bash
docker exec -it backtester_postgres psql -U backtester -d backtester -c \
  "SELECT COUNT(*) FROM backtester.optimization_results;"

# Должно быть минимум 1 запись если тест прошёл
```

---

## 🔍 Troubleshooting

### Ошибка: "ModuleNotFoundError: No module named 'optuna'"

**Решение:**
```bash
docker-compose down
docker-compose build --no-cache backtester-web
docker-compose up -d
```

### Ошибка: "relation 'backtester.optimization_results' does not exist"

**Решение:**
```bash
# Применить миграцию БД (см. шаг 5 выше)
docker exec -it backtester_postgres psql -U backtester -d backtester < /docker-entrypoint-initdb.d/init.sql
```

Или вручную создать таблицу (SQL из шага 5).

### Ошибка: "Failed to check optimizer access"

**Решение:**
```bash
# Проверьте что ваш ID вшит в код
docker exec -it backtester_web grep -n "297936848" /app/database.py

# Должно показать строку с HARDCODED_OPTIMIZER_ADMINS
```

### Не приходят Telegram уведомления

**Проверка:**
```bash
# 1. Проверьте что бот запущен
docker ps | grep telegram

# 2. Проверьте токен
docker exec backtester_telegram_bot env | grep TELEGRAM_BOT_TOKEN

# 3. Проверьте логи
docker logs backtester_telegram_bot | tail -50

# 4. Проверьте что вы подписаны на бота
# Напишите /start боту в Telegram
```

### Оптимизация зависает

**Решение:**
```bash
# Проверьте логи
docker logs -f backtester_web

# Проверьте ресурсы
docker stats

# Перезапустите если нужно
docker restart backtester_web
```

---

## 📊 Мониторинг после deployment

### Логи в реальном времени

```bash
# Web приложение
docker logs -f backtester_web

# Telegram бот
docker logs -f backtester_telegram_bot

# Все сервисы
docker-compose logs -f
```

### Статистика ресурсов

```bash
docker stats

# Если нужно ограничить ресурсы:
# Отредактируйте docker-compose.yml:
services:
  backtester-web:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

### Мониторинг очереди оптимизации

```bash
# Статус очереди
watch -n 5 'curl -s http://localhost:8000/api/optimize/queue | jq'

# История оптимизаций
curl http://localhost:8000/api/optimize/history?limit=10 | jq
```

---

## 🎯 Production рекомендации

### 1. SSL/HTTPS

Если используете в production, настройте SSL через Traefik:
```bash
docker-compose -f docker-compose.traefik.yml up -d
```

### 2. Backup БД

```bash
# Автоматический backup каждый день
crontab -e

# Добавьте:
0 3 * * * docker exec backtester_postgres pg_dump -U backtester backtester > /backups/backtester_$(date +\%Y\%m\%d).sql
```

### 3. Мониторинг

Рассмотрите добавление:
- Prometheus + Grafana для метрик
- Sentry для error tracking
- Uptime monitoring

### 4. Rate limiting

Если открываете наружу, добавьте rate limiting в nginx/traefik.

---

## ✅ Checklist финальной проверки

- [ ] `git pull` выполнен
- [ ] `docker-compose build --no-cache` выполнен
- [ ] БД миграция применена
- [ ] Все контейнеры запущены (`docker ps`)
- [ ] Health check проходит (`curl localhost:8000/health`)
- [ ] Web UI доступен (`localhost:8000/optimize`)
- [ ] Тестовая оптимизация запущена успешно
- [ ] Telegram уведомления приходят
- [ ] Логи не содержат критических ошибок
- [ ] Ресурсы сервера в норме (`docker stats`)

---

**После всех шагов система готова к production использованию! 🚀**
