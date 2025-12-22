# ⚡ Quick Start - Strategy Optimization

## 1️⃣ Дать себе доступ (один раз)

```bash
# Узнайте ваш Telegram ID через @userinfobot
# Затем:

docker exec -it backtester_postgres psql -U backtester -d backtester -c \
  "UPDATE market_data.bot_subscribers SET is_optimizer_admin = TRUE WHERE user_id = YOUR_TELEGRAM_ID;"
```

## 2️⃣ Запустить оптимизацию

### ✅ С индикаторами (RSI + EMA)

```bash
docker exec -it backtester_web python main.py \
  --optimize \
  --optimization-config optimization_config_with_indicators.json \
  --user-id YOUR_TELEGRAM_ID \
  --n-trials 150
```

**Оптимизирует:**
- RSI параметры (period, oversold/overbought)
- EMA параметры (fast/slow periods)
- Take Profit, DCA настройки

---

### ✅ Без индикаторов (чистая DCA)

```bash
docker exec -it backtester_web python main.py \
  --optimize \
  --optimization-config optimization_config_no_indicators.json \
  --user-id YOUR_TELEGRAM_ID \
  --n-trials 200
```

**Оптимизирует:**
- Take Profit / Stop Loss уровни
- DCA параметры (max_orders, step, multiplier, progression)
- Размер первого ордера

---

### ✅ Через Web UI (самый удобный)

1. Откройте: http://localhost:8000/optimize
2. Введите Telegram User ID
3. Настройте параметры
4. Нажмите "Start Optimization"
5. Следите за прогрессом в Telegram

---

## 3️⃣ Результаты

**Telegram уведомления:**
- Старт оптимизации
- Прогресс каждые 20%
- Финальные результаты с лучшими параметрами

**Web UI:**
```
http://localhost:8000/optimization-results/TASK_ID
```

**API:**
```bash
curl http://localhost:8000/api/optimize/status/TASK_ID
curl http://localhost:8000/api/optimize/results/TASK_ID
```

---

## 4️⃣ Сохранить лучшую конфигурацию

```bash
curl -X POST http://localhost:8000/api/optimize/save-config/TASK_ID \
  -H "X-User-ID: YOUR_TELEGRAM_ID"
```

Или через Web UI: кнопка "Save Best Config"

---

## 📊 Время выполнения

- 100 trials ≈ 12-15 минут
- 200 trials ≈ 25-30 минут

---

## 📚 Полная документация

См. `DOCKER_OPTIMIZATION_GUIDE.md`
