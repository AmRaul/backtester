# Dual Timeframe Backtesting

## Проблема

При бэктестинге на крупных таймфреймах (15m, 1h, 4h) возникает проблема **intrabar execution** - внутри одной свечи может произойти несколько событий:

### Пример проблемы:
```
15-минутная свеча:
- open: 100
- high: 105
- low: 98
- close: 102

Позиция: LONG от 100, TP=105, SL=95

Что происходит внутри свечи:
1. 10:00 - Цена 100 → Вход в позицию
2. 10:03 - Цена 105 → TP сработал! Закрытие.
3. 10:05 - Цена 104 → Новый сигнал входа
4. 10:07 - Цена 99  → Должен сработать новый SL!
5. 10:14 - Цена 102 → Закрытие свечи

❌ БЕЗ DUAL TF: Система видит только close=102, пропускает 2 сделки
✅ С DUAL TF: Система обрабатывает каждую минуту, видит все 2 сделки
```

## Решение

**Multi-Timeframe Backtesting** - индикаторы на стратегическом таймфрейме (15m), исполнение на execution таймфрейме (1m).

### Архитектура:

```
┌─────────────────────────────────────────┐
│  STRATEGY TIMEFRAME (15m)               │
│  - Индикаторы: EMA, RSI, MACD          │
│  - Сигналы входа                        │
│  - Условия стратегии                    │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  EXECUTION TIMEFRAME (1m)               │
│  - Точная проверка TP/SL                │
│  - Реальная последовательность цен      │
│  - Множественные входы/выходы           │
└─────────────────────────────────────────┘
```

## Использование

### 1. Конфигурация

Добавьте параметр `execution_timeframe` в конфиг:

```json
{
  "timeframe": "15m",              // Для индикаторов
  "execution_timeframe": "1m",     // Для исполнения (опционально)

  "data_source": {
    "type": "api",
    "api": {
      "exchange": "binance",
      "symbol": "BTC/USDT"
    }
  }
}
```

**Примечание:**
- Если `execution_timeframe` не указан → single timeframe режим (как раньше)
- Если `execution_timeframe` == `timeframe` → single timeframe режим
- Если `execution_timeframe` != `timeframe` → dual timeframe режим ✅

### 2. Запуск

```python
from backtester import Backtester

# Создаем бэктестер с dual timeframe конфигом
bt = Backtester(config_path='config_dual_timeframe_example.json')

# Запускаем бэктест
results = bt.run_backtest()
```

### 3. Тестовый скрипт

```bash
python test_dual_timeframe.py
```

## Поддерживаемые комбинации

| Strategy TF | Execution TF | Соотношение | Рекомендация |
|------------|--------------|-------------|--------------|
| 15m        | 1m           | 15:1        | ✅ Отлично   |
| 1h         | 5m           | 12:1        | ✅ Отлично   |
| 4h         | 15m          | 16:1        | ✅ Хорошо    |
| 1d         | 1h           | 24:1        | ✅ Хорошо    |
| 15m        | 5m           | 3:1         | ⚠️ Мало смысла |

## Технические детали

### Как это работает

1. **Загрузка данных** (`data_loader.py`):
   ```python
   execution_data, strategy_data = load_dual_timeframe(
       execution_timeframe='1m',
       strategy_timeframe='15m'
   )
   ```

2. **Обработка тиков** (`backtester.py`):
   ```python
   for tick_1m in execution_data:
       # Находим родительскую 15m свечу (последнюю ЗАКРЫТУЮ!)
       parent_15m = get_parent_candle_index(tick_1m.timestamp)

       # Передаем оба таймфрейма в стратегию
       process_tick_dual(tick_1m, parent_15m)
   ```

3. **Стратегия** (`strategy.py`):
   ```python
   def process_tick_dual(exec_data_1m, strategy_data_15m):
       # Индикаторы на 15m
       ema = calculate_ema(strategy_data_15m)

       # Сигнал входа на 15m
       if should_enter(strategy_data_15m):
           # Но входим по 1m цене!
           open_position(exec_data_1m.close)

       # TP/SL проверяем по 1m цене (точно!)
       if exec_data_1m.close >= tp_price:
           close_position(exec_data_1m.close)
   ```

### Look-Ahead Bias Protection

⚠️ **Важно:** Используем только ЗАКРЫТЫЕ свечи стратегического таймфрейма!

```python
# ❌ НЕПРАВИЛЬНО (look-ahead bias):
# Используем текущую 15m свечу которая ещё не закрылась
current_15m = strategy_data[current_time]

# ✅ ПРАВИЛЬНО (no look-ahead bias):
# Используем последнюю ЗАКРЫТУЮ 15m свечу
parent_idx = get_parent_candle_index(current_time)
last_closed_15m = strategy_data[parent_idx]
```

## Преимущества

✅ **Точность**: Видим реальную последовательность событий внутри крупной свечи
✅ **Множественные сделки**: Можем открыть и закрыть несколько позиций за одну 15m свечу
✅ **Реалистичность**: Результаты бэктеста ближе к реальной торговле
✅ **Обратная совместимость**: Single timeframe режим работает как раньше
✅ **Гибкость**: Любые комбинации таймфреймов

## Недостатки

❌ **Скорость**: Медленнее в 15x раз (для 15m/1m)
❌ **Объем данных**: Нужно загружать в 15x больше данных
❌ **API лимиты**: Больше запросов к бирже

## Эмуляция TradingView Bar Magnifier

Наша реализация **ТОЧНО КОПИРУЕТ** логику TradingView Bar Magnifier:

### ✅ Что совпадает с Bar Magnifier

| Аспект | Bar Magnifier | Наша реализация |
|--------|---------------|-----------------|
| **Данные** | Использует 1m данные для intrabar | ✅ `execution_timeframe="1m"` |
| **Индикаторы** | Считаются на таймфрейме графика | ✅ На `strategy_timeframe` |
| **Сигналы входа** | Проверяются при ЗАКРЫТИИ strategy свечи | ✅ Только при `is_new_strategy_bar` |
| **TP/SL** | Проверяются на КАЖДОЙ intrabar цене | ✅ На каждой execution свече |
| **calc_on_order_fills** | Пересчет после исполнения | ✅ `self.calc_on_order_fills` |
| **Множественные сделки** | Возможны внутри свечи | ✅ Если `calc_on_order_fills=True` |

### calc_on_order_fills (эмуляция PineScript)

```python
# В конфиге можно включить:
strategy = TradingStrategy(config)
strategy.calc_on_order_fills = True  # Как в PineScript

# Теперь после каждого TP/SL:
# 1. Позиция закрывается
# 2. СРАЗУ проверяется новый сигнал входа
# 3. Можно открыть новую позицию на той же strategy свече
```

**По умолчанию:** `calc_on_order_fills=False` (как в PineScript)

### Сравнение режимов

**Single Timeframe (15m only):**
```
Данные: 2880 свечей (30 дней * 96 свечей/день)
Скорость: 2880 тиков обработано
Точность: Средняя (не видит intrabar события)
Сигналы: Проверяются на каждой свече
```

**Dual Timeframe (15m strategy / 1m execution) - Bar Magnifier:**
```
Данные: 43,200 свечей (30 дней * 1440 минут/день)
Скорость: 43,200 тиков обработано (15x медленнее)
Точность: Высокая (видит каждую минуту)
Сигналы: Проверяются ТОЛЬКО при новой 15m свече ✅
TP/SL: Проверяются КАЖДУЮ 1m ✅
```

## FAQ

### Q: Обязательно ли использовать dual timeframe?
**A:** Нет. Если не указать `execution_timeframe`, система работает в single timeframe режиме.

### Q: Какой execution timeframe выбрать?
**A:** Рекомендация: в 10-15 раз меньше strategy timeframe. Например:
- 15m → 1m
- 1h → 5m
- 4h → 15m

### Q: Будет ли работать с CSV данными?
**A:** Пока только с API. Для CSV нужно загрузить оба таймфрейма отдельно.

### Q: Влияет ли на индикаторы?
**A:** Нет. Индикаторы считаются на strategy timeframe как обычно.

### Q: Можно ли использовать разные биржи?
**A:** Да! Exchange берется из конфига `data_source.api.exchange`.

## Примеры конфигураций

См. файл `config_dual_timeframe_example.json`:
- `dual_tf_btc_15m_1m` - BTC на 15m/1m
- `dual_tf_eth_1h_5m` - ETH на 1h/5m

## Автор

Разработано для корректного бэктестинга с учетом intrabar execution.

---

**Версия:** 1.0
**Дата:** 2024-12-07
