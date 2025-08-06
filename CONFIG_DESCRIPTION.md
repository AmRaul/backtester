# Описание полей конфигурации бэктестера

## Основные параметры

| Поле | Описание | Пример |
|------|----------|--------|
| `start_balance` | Начальный баланс в USD | `1000` |
| `leverage` | Кредитное плечо (1 = без плеча) | `1` |
| `order_type` | Тип позиции: "long" или "short" | `"long"` |

## Условия входа в позицию

| Поле | Описание | Возможные значения |
|------|----------|-------------------|
| `entry_conditions.type` | Тип входа | `"manual"` (ручной по цене) |
| `entry_conditions.trigger` | Триггер входа | `"price_drop"` (падение) или `"price_rise"` (рост) |
| `entry_conditions.percent` | Процент падения/роста для входа | `2` (2%) |

## Параметры первого ордера

| Поле | Описание | Пример |
|------|----------|--------|
| `first_order.amount_percent` | Процент баланса для первого ордера | `10` (10%) или `null` |
| `first_order.amount_fixed` | Фиксированная сумма в USD | `100` ($100) или `null` |
| `first_order.risk_percent` | Процент риска от баланса | `null` (не используется) |

**Приоритет:** `amount_fixed` > `amount_percent` > `10% по умолчанию`

## DCA (Dollar Cost Averaging)

| Поле | Описание | Пример |
|------|----------|--------|
| `dca.enabled` | Включить DCA (покупка при падении) | `true` |
| `dca.max_orders` | Максимальное количество DCA ордеров | `5` |

### Мартингейл

| Поле | Описание | Возможные значения |
|------|----------|-------------------|
| `dca.martingale.enabled` | Включить мартингейл | `true`/`false` |
| `dca.martingale.multiplier` | Множитель для следующего ордера | `2.0` (удвоение) |
| `dca.martingale.progression` | Тип прогрессии | `"exponential"`, `"linear"`, `"fibonacci"` |

### Шаг цены

| Поле | Описание | Возможные значения |
|------|----------|-------------------|
| `dca.step_price.type` | Тип шага | `"fixed_percent"`, `"dynamic_percent"`, `"atr_based"` |
| `dca.step_price.value` | Процент шага для DCA | `1.5` (1.5%) |
| `dca.step_price.dynamic_multiplier` | Множитель для динамического шага | `1.0` |
| `dca.step_price.atr_multiplier` | Множитель ATR для шага | `null` (не используется) |

## Take Profit (закрытие по прибыли)

| Поле | Описание | Пример |
|------|----------|--------|
| `take_profit.enabled` | Включить Take Profit | `true` |
| `take_profit.percent` | Процент прибыли для закрытия | `5` (5%) |

### Trailing Stop

| Поле | Описание | Пример |
|------|----------|--------|
| `take_profit.trailing.enabled` | Включить trailing stop | `false` |
| `take_profit.trailing.activation_percent` | Процент активации trailing | `3` (3%) |
| `take_profit.trailing.trail_percent` | Процент отставания trailing | `1` (1%) |

## Stop Loss (закрытие по убытку)

| Поле | Описание | Пример |
|------|----------|--------|
| `stop_loss.enabled` | Включить Stop Loss | `true` |
| `stop_loss.percent` | Процент убытка для закрытия | `10` (10%) |

### Trailing Stop

| Поле | Описание | Пример |
|------|----------|--------|
| `stop_loss.trailing.enabled` | Включить trailing stop | `false` |
| `stop_loss.trailing.activation_percent` | Процент активации trailing | `2` (2%) |
| `stop_loss.trailing.trail_percent` | Процент отставания trailing | `0.5` (0.5%) |

## Риск-менеджмент

| Поле | Описание | Пример |
|------|----------|--------|
| `risk_management.max_drawdown_percent` | Максимальная просадка в процентах | `20` (20%) |
| `risk_management.max_open_positions` | Максимальное количество открытых позиций | `1` |
| `risk_management.daily_loss_limit` | Дневной лимит убытков в USD | `null` (не ограничено) |

## Торговые параметры

| Поле | Описание | Возможные значения |
|------|----------|-------------------|
| `symbol` | Торговая пара | `"BTCUSDT"`, `"ETHUSDT"` |
| `timeframe` | Таймфрейм данных | `"1m"`, `"5m"`, `"15m"`, `"1h"`, `"4h"`, `"1d"` |

## Источник данных

| Поле | Описание | Пример |
|------|----------|--------|
| `data_source.type` | Тип источника | `"csv"` или `"api"` |
| `data_source.file` | Путь к CSV файлу | `"data/BTCUSDT_1h.csv"` |

### API настройки

| Поле | Описание | Пример |
|------|----------|--------|
| `data_source.api.exchange` | Биржа для API | `"binance"` |
| `data_source.api.symbol` | Символ для API | `"BTC/USDT"` |
| `data_source.api.auto_save` | Автосохранение данных в CSV | `true` |

## Период тестирования

| Поле | Описание | Пример |
|------|----------|--------|
| `start_date` | Начальная дата | `null` (с начала данных) или `"2025-01-01"` |
| `end_date` | Конечная дата | `null` (до конца данных) или `"2025-12-31"` |

## Примеры настроек

### Консервативная стратегия
```json
{
  "entry_conditions": {
    "trigger": "price_drop",
    "percent": 3
  },
  "take_profit": {
    "percent": 4
  },
  "stop_loss": {
    "percent": 15
  }
}
```

### Агрессивная стратегия
```json
{
  "entry_conditions": {
    "trigger": "price_drop", 
    "percent": 1
  },
  "take_profit": {
    "percent": 2
  },
  "stop_loss": {
    "percent": 25
  }
}
```

### Стратегия с фиксированной суммой
```json
{
  "first_order": {
    "amount_percent": null,
    "amount_fixed": 100,
    "risk_percent": null
  },
  "entry_conditions": {
    "trigger": "price_drop",
    "percent": 2
  }
}
```

### Стратегия с процентом от баланса
```json
{
  "first_order": {
    "amount_percent": 15,
    "amount_fixed": null,
    "risk_percent": null
  },
  "entry_conditions": {
    "trigger": "price_drop",
    "percent": 3
  }
}
``` 