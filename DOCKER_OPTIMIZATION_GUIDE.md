# 🐳 Docker Guide - Strategy Optimization

## Быстрый старт

### 1️⃣ Настройка доступа к оптимизатору

Сначала дайте вашему Telegram ID доступ к функции оптимизации:

```bash
# Узнайте ваш Telegram User ID через бота (@userinfobot)
# Затем выполните SQL в контейнере postgres:

docker exec -it backtester_postgres psql -U backtester -d backtester -c \
  "UPDATE market_data.bot_subscribers SET is_optimizer_admin = TRUE WHERE user_id = YOUR_TELEGRAM_ID;"

# Пример:
docker exec -it backtester_postgres psql -U backtester -d backtester -c \
  "UPDATE market_data.bot_subscribers SET is_optimizer_admin = TRUE WHERE user_id = 123456789;"
```

Проверка доступа:
```bash
docker exec -it backtester_postgres psql -U backtester -d backtester -c \
  "SELECT user_id, username, is_optimizer_admin FROM market_data.bot_subscribers WHERE user_id = YOUR_TELEGRAM_ID;"
```

---

## 2️⃣ Запуск оптимизации (3 способа)

### Способ A: Через Web UI (рекомендуется)

1. Откройте http://localhost:8000/optimize
2. Введите ваш Telegram User ID
3. Настройте параметры:
   - Symbol (например FARTCOIN/USDT)
   - Number of trials (рекомендуется 100-200)
   - Параметры для оптимизации (RSI, TP, DCA и т.д.)
4. Нажмите "Start Optimization"
5. Получите Telegram уведомление и следите за прогрессом

**Преимущества:**
- Удобный интерфейс
- Визуализация результатов
- История оптимизаций

---

### Способ B: Через Docker CLI

**Вариант 1: С индикаторами (RSI, EMA)**

```bash
docker exec -it backtester_web python main.py \
  --optimize \
  --optimization-config optimization_config_with_indicators.json \
  --user-id YOUR_TELEGRAM_ID \
  --n-trials 150
```

**Вариант 2: Без индикаторов (чистая DCA стратегия)**

```bash
docker exec -it backtester_web python main.py \
  --optimize \
  --optimization-config optimization_config_no_indicators.json \
  --user-id YOUR_TELEGRAM_ID \
  --n-trials 200
```

**Вариант 3: Свой конфиг**

```bash
# Создайте свой конфиг на хосте:
nano my_optimization.json

# Скопируйте в контейнер:
docker cp my_optimization.json backtester_web:/app/

# Запустите:
docker exec -it backtester_web python main.py \
  --optimize \
  --optimization-config my_optimization.json \
  --user-id YOUR_TELEGRAM_ID \
  --n-trials 100
```

---

### Способ C: Через API (для автоматизации)

```bash
curl -X POST http://localhost:8000/api/optimize/start \
  -H "Content-Type: application/json" \
  -H "X-User-ID: YOUR_TELEGRAM_ID" \
  -d '{
    "base_config": {
      "symbol": "FARTCOIN/USDT",
      "timeframe": "15m",
      "start_balance": 10000,
      "order_type": "long",
      "data_source": {
        "type": "api",
        "api": {
          "exchange": "binance",
          "symbol": "FART/USDT",
          "market_type": "spot"
        }
      },
      "dca": {"enabled": true, "max_orders": 5},
      "take_profit": {"enabled": true, "target_percent": 3.0}
    },
    "optimization_params": {
      "take_profit.target_percent": [1.0, 2.0, 3.0, 4.0, 5.0],
      "dca.max_orders": [3, 5, 7, 10]
    },
    "n_trials": 100
  }'
```

---

## 3️⃣ Примеры конфигураций

### 📊 С индикаторами (`optimization_config_with_indicators.json`)

**Оптимизирует:**
- RSI period: [7, 10, 14, 21]
- RSI oversold: [20, 25, 30, 35, 40]
- EMA fast: [5, 7, 9, 12]
- EMA slow: [15, 21, 26, 30]
- Take profit: 1% - 5%
- DCA параметры

**Подходит для:**
- Технический анализ
- Поиск оптимальных индикаторов
- Стратегии на основе перекупленности/перепроданности

**Использование:**
```bash
docker exec -it backtester_web python main.py \
  --optimize \
  --optimization-config optimization_config_with_indicators.json \
  --user-id 123456789 \
  --n-trials 150
```

---

### 💰 Без индикаторов (`optimization_config_no_indicators.json`)

**Оптимизирует:**
- Take profit: 1% - 8%
- Stop loss: 5% - 25%
- DCA max orders: [3, 5, 7, 10, 15]
- DCA step: [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
- DCA multiplier: 1.0 - 2.5
- DCA progression: exponential / linear / fibonacci
- First order size: [5, 8, 10, 12, 15, 20, 25]%

**Подходит для:**
- Чистая DCA стратегия
- HODLing с усреднением
- Поиск оптимального риск-менеджмента

**Использование:**
```bash
docker exec -it backtester_web python main.py \
  --optimize \
  --optimization-config optimization_config_no_indicators.json \
  --user-id 123456789 \
  --n-trials 200
```

---

## 4️⃣ Мониторинг процесса

### Логи оптимизации в реальном времени:

```bash
# Логи web приложения
docker logs -f backtester_web

# Логи Telegram бота (уведомления)
docker logs -f backtester_telegram_bot

# Статус очереди через API
curl http://localhost:8000/api/optimize/queue
```

### Проверка статуса задачи:

```bash
# Получить task_id из вывода команды или Telegram
curl http://localhost:8000/api/optimize/status/TASK_ID
```

### Просмотр результатов:

```bash
# Через браузер
http://localhost:8000/optimization-results/TASK_ID

# Через API
curl http://localhost:8000/api/optimize/results/TASK_ID

# История всех оптимизаций
curl http://localhost:8000/api/optimize/history?limit=20
```

---

## 5️⃣ Telegram уведомления

При запуске оптимизации вы получите:

**Старт:**
```
🚀 Запуск оптимизации для FARTCOIN/USDT
🔬 Trials: 100
⏱️ Примерное время: ~15 мин
```

**Прогресс (каждые 20%):**
```
📊 Прогресс оптимизации: 40/100 (40%)

🏆 Лучший результат:
✅ Успешных сделок: 87
📈 Win Rate: 72.5%
💰 Доходность: 145.30%
⭐Score: 234.56
```

**Завершение:**
```
✅ Оптимизация завершена!

🏆 Лучшие результаты:
✅ Успешных сделок: 92
📊 Всего сделок: 120
📈 Win Rate: 76.7%
💰 Доходность: 178.25%
📉 Max DD: 12.45%
⚡ Profit Factor: 3.45
📐 Sharpe Ratio: 2.15

🔧 Оптимальные параметры:
• indicators.rsi.oversold: 25
• take_profit.target_percent: 3.5
• dca.max_orders: 7
• dca.step_percent: 2.0

⏱️ Время: 14.3 мин
```

---

## 6️⃣ Сохранение лучшей конфигурации

### Через Web UI:
1. Откройте страницу результатов
2. Нажмите "Save Best Config"
3. Конфиг сохранится в `strategy_configs`

### Через API:
```bash
curl -X POST http://localhost:8000/api/optimize/save-config/TASK_ID \
  -H "X-User-ID: YOUR_TELEGRAM_ID"
```

### Через CLI:
```bash
# Результаты автоматически сохраняются в:
# - БД: backtester.optimization_results
# - JSON: results/optimization_XXXXXXXX.json

# Скопировать JSON на хост:
docker cp backtester_web:/app/results/optimization_12345678.json ./
```

---

## 7️⃣ Пересборка после изменений

Если вы меняли код оптимизатора:

```bash
# Остановить сервисы
docker-compose down

# Пересобрать образы
docker-compose build backtester-web

# Запустить
docker-compose up -d

# Проверить логи
docker logs -f backtester_web
```

---

## 8️⃣ Производительность и ограничения

### Настройка производительности:

Можно изменить в конфиге (`optimization_settings`):

```json
{
  "optimization_settings": {
    "n_trials": 100,              // Количество попыток (больше = лучше, но дольше)
    "max_parallel_backtests": 4,  // Параллельные бэктесты (зависит от CPU)
    "optimization_metric": "custom_score",  // Метрика оптимизации
    "timeout_minutes": 60         // Таймаут (не реализовано)
  }
}
```

### Ограничения:

- **Очередь**: Максимум 1 оптимизация одновременно (другие ждут в очереди)
- **Параллельность**: 4 бэктеста одновременно внутри оптимизации
- **Время**: ~30 сек на trial → 100 trials ≈ 12-15 минут
- **Память**: ~500MB RAM на оптимизацию

### Мониторинг ресурсов Docker:

```bash
# Статистика контейнеров
docker stats

# Если тормозит, можно ограничить ресурсы в docker-compose.yml:
services:
  backtester-web:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

---

## 9️⃣ Troubleshooting

### Ошибка: "Unauthorized - user_id required"

**Решение:**
```bash
# Проверьте что вы передали user_id
# Web UI: заполните поле "Telegram User ID"
# CLI: добавьте --user-id
# API: добавьте header X-User-ID
```

### Ошибка: "Forbidden - optimizer access denied"

**Решение:**
```bash
# Дайте себе доступ через SQL:
docker exec -it backtester_postgres psql -U backtester -d backtester -c \
  "UPDATE market_data.bot_subscribers SET is_optimizer_admin = TRUE WHERE user_id = YOUR_ID;"
```

### Оптимизация зависла

**Решение:**
```bash
# Проверьте логи
docker logs -f backtester_web

# Перезапустите контейнер
docker restart backtester_web

# Проверьте статус очереди
curl http://localhost:8000/api/optimize/queue
```

### Не приходят Telegram уведомления

**Проверка:**
```bash
# 1. Проверьте что бот запущен
docker ps | grep telegram

# 2. Проверьте логи бота
docker logs backtester_telegram_bot

# 3. Проверьте что вы подписаны на бота
# Напишите /start боту в Telegram

# 4. Проверьте переменную окружения
docker exec backtester_telegram_bot env | grep TELEGRAM_BOT_TOKEN
```

---

## 🎯 Best Practices

1. **Начните с малого**: 50-100 trials для первого запуска
2. **Walk-forward validation**: После оптимизации протестируйте на новых данных
3. **Не переоптимизируйте**: Лучший результат на истории ≠ лучший в будущем
4. **Используйте разные периоды**: Оптимизируйте на одном периоде, тестируйте на другом
5. **Следите за overfitting**: Если винрейт > 90% - скорее всего overfitting
6. **Комбинируйте метрики**: Не только прибыль, но и Sharpe Ratio, Max DD
7. **Сохраняйте топ-10**: Не только лучший, но и топ-10 результатов
8. **Документируйте**: Записывайте параметры и результаты

---

## 📚 Дополнительные ресурсы

- **Документация Optuna**: https://optuna.readthedocs.io/
- **Примеры конфигов**: `optimization_config_*.json`
- **Web UI**: http://localhost:8000/optimize
- **API docs**: http://localhost:8000/health

---

**Готово! Теперь вы можете автоматически находить лучшие параметры для любой монеты! 🚀**
