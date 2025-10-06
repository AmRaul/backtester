# 📈 Backtester - Модуль бэктестирования алгоритмических стратегий

Комплексный инструмент для бэктестирования торговых стратегий с поддержкой DCA (Dollar Cost Averaging), стратегий Мартингейл и различных типов ордеров.

## 🚀 Возможности

- **Поддержка Long/Short позиций** - торговля в обе стороны
- **DCA (Dollar Cost Averaging)** - усреднение позиций при неблагоприятном движении цены
- **Стратегия Мартингейл** - увеличение размера ордеров при усреднении
- **Гибкая настройка** - все параметры через JSON конфигурацию
- **Подробная отчетность** - статистика, графики, анализ рисков
- **Загрузка данных** - из CSV файлов и API через CCXT (100+ бирж)
- **Веб-интерфейс** - современный UI для управления бэктестами
- **Docker контейнеризация** - простое развертывание и масштабирование
 
## 📦 Установка

### 🐳 Docker (рекомендуется)

1. **Клонируйте проект:**
```bash
git clone <repository-url>
cd backtester
```


2. **Запустите веб-интерфейс:**
```bash
./docker-run.sh web
```

3. **Откройте браузер:** http://localhost:8000

### 🐍 Локальная установка

1. **Клонируйте проект:**
```bash
git clone <repository-url>
cd backtester
```

2. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

> **Примечание:** Для загрузки данных с бирж требуется пакет `ccxt`. Если он не установился автоматически:
> ```bash
> pip install ccxt
> ```

## 🎯 Быстрый старт

1. **Создайте образец данных для тестирования:**
```bash
python main.py --create-sample-data
```

2. **Запустите базовый бэктест:**
```bash
python main.py
```

3. **Запустите с подробным выводом и сохранением результатов:**
```bash
python main.py --verbose --save-results --generate-report
```

## 🐳 Docker запуск (рекомендуется)

### Веб-интерфейс
```bash
# Запуск веб-интерфейса на http://localhost:8000
./docker-run.sh web

# Или с помощью docker-compose
docker-compose up -d backtester-web
```

### CLI в Docker
```bash
# Показать помощь
./docker-run.sh cli --help

# Запустить бэктест
./docker-run.sh cli --strategy conservative_long

# Загрузить данные с биржи
./docker-run.sh cli --download-data --exchange binance
```

### Управление Docker
```bash
./docker-run.sh build    # Собрать образы
./docker-run.sh stop     # Остановить все сервисы
./docker-run.sh logs     # Показать логи
./docker-run.sh clean    # Очистить все контейнеры
```

### Решение проблем с Docker

Если возникают проблемы с сетью при сборке Docker образа:

```bash
# Используйте минимальную версию без системных пакетов
./docker-run.sh build --minimal
./docker-run.sh web --minimal
```

Подробное руководство по решению проблем: [DOCKER_TROUBLESHOOTING.md](DOCKER_TROUBLESHOOTING.md)

### 🌐 Загрузка данных с бирж

1. **Посмотрите доступные биржи:**
```bash
python main.py --list-exchanges
```

2. **Загрузите данные с биржи:**
```bash
python main.py --download-data --exchange binance --symbol-api BTC/USDT --timeframe-api 1h
```

3. **Запустите бэктест с данными из API:**
```bash
python main.py --strategy binance_btc_1h
```

## 🌐 Веб-интерфейс

Современный веб-интерфейс предоставляет удобное управление бэктестами через браузер:

### Основные возможности:
- 📊 **Интерактивные графики** - кривая эквити, распределение PnL, просадка
- ⚙️ **Визуальный конфигуратор** - настройка стратегий через формы
- 🚀 **Асинхронные бэктесты** - запуск в фоновом режиме с отслеживанием прогресса
- 📈 **Управление данными** - загрузка с бирж, просмотр доступных символов
- 📋 **История результатов** - сохранение и сравнение бэктестов
- 📱 **Адаптивный дизайн** - работает на всех устройствах

### Доступ:
```bash
# Запуск веб-интерфейса
./docker-run.sh web

# Откройте в браузере
http://localhost:8000
```

### Страницы:
- **Главная** - обзор возможностей и быстрый старт
- **Конфигурация** - настройка параметров стратегии
- **Результаты** - просмотр и анализ бэктестов
- **API** - REST endpoints для интеграции

## ⚙️ Конфигурация

Основные параметры настраиваются в файле `config.json`. Новая расширенная структура:

```json
{
  "start_balance": 1000,           // Начальный баланс
  "leverage": 1,                   // Плечо (1-10)
  "order_type": "long",            // Тип ордеров: "long" или "short"
  
  "entry_conditions": {
    "type": "manual",              // Тип входа в позицию
    "trigger": "price_drop",       // Триггер: "price_drop" или "price_rise"
    "percent": 2                   // Процент изменения для входа
  },
  
  "first_order": {
    "amount_percent": 10,          // Процент от баланса для первого ордера
    "amount_fixed": null,          // Фиксированная сумма (альтернатива проценту)
    "risk_percent": null           // Процент риска от баланса
  },
  
  "dca": {
    "enabled": true,               // Включить DCA
    "max_orders": 5,               // Максимум DCA ордеров
    "martingale": {
      "enabled": true,             // Включить мартингейл
      "multiplier": 2.0,           // Мультипликатор размера ордера
      "progression": "exponential" // Тип прогрессии: exponential/linear/fibonacci
    },
    "step_price": {
      "type": "fixed_percent",     // Тип шага: fixed_percent/dynamic_percent/atr_based
      "value": 1.5,                // Базовое значение шага в процентах
      "dynamic_multiplier": 1.0,   // Мультипликатор для динамического шага
      "atr_multiplier": null       // Мультипликатор ATR (для atr_based)
    }
  },
  
  "take_profit": {
    "enabled": true,               // Включить take profit
    "percent": 5,                  // Процент take profit
    "trailing": {
      "enabled": false,            // Включить trailing take profit
      "activation_percent": 3,     // Процент активации trailing
      "trail_percent": 1           // Процент отступа trailing
    }
  },
  
  "stop_loss": {
    "enabled": true,               // Включить stop loss
    "percent": 10,                 // Процент stop loss
    "trailing": {
      "enabled": false,            // Включить trailing stop loss
      "activation_percent": 2,     // Процент активации trailing
      "trail_percent": 0.5         // Процент отступа trailing
    }
  },
  
  "risk_management": {
    "max_drawdown_percent": 20,    // Максимальная просадка в процентах
    "max_open_positions": 1,       // Максимум открытых позиций
    "daily_loss_limit": null       // Дневной лимит убытков
  }
}
```

## 🌐 Поддерживаемые биржи

Через CCXT интеграцию поддерживается **100+ криптобирж**, включая:

### Популярные биржи:
- **Binance** - крупнейшая криптобиржа
- **OKX** - высокая ликвидность
- **Bybit** - деривативы и спот
- **KuCoin** - широкий выбор альткоинов
- **Coinbase Pro** - регулируемая биржа США
- **Kraken** - европейская биржа
- **Huobi** - азиатская биржа
- **Gate.io** - DeFi токены

### Доступные таймфреймы:
- `1m`, `3m`, `5m`, `15m`, `30m` - минутные
- `1h`, `2h`, `4h`, `6h`, `8h`, `12h` - часовые  
- `1d`, `3d`, `1w`, `1M` - дневные и выше

### Команды для работы с API:
```bash
# Посмотреть все доступные биржи
python main.py --list-exchanges

# Информация о конкретной бирже
python main.py --exchange-info binance

# Загрузить данные BTC/USDT с Binance за последние 30 дней
python main.py --download-data --exchange binance --symbol-api BTC/USDT --timeframe-api 1h
```

## 📊 Формат данных

CSV файл должен содержать следующие колонки:
```csv
timestamp,open,high,low,close,volume
2023-01-01 00:00:00,30000.00,30100.00,29900.00,30050.00,125.45
2023-01-01 00:15:00,30050.00,30200.00,30000.00,30150.00,98.32
...
```

## 🎮 Использование

### Основные команды

```bash
# Базовый запуск
python main.py

# Использование своего конфига
python main.py --config my_config.json

# Использование готовой стратегии
python main.py --strategy aggressive_martingale

# Подробный вывод
python main.py --verbose

# Сохранение результатов
python main.py --save-results

# Генерация полного отчета с графиками
python main.py --generate-report

# Создание образца данных
python main.py --create-sample-data

# Создание отчета из существующих результатов
python main.py --report-only results.json

# Работа с API и биржами
python main.py --list-exchanges                    # Список доступных бирж
python main.py --exchange-info binance             # Информация о бирже
python main.py --download-data --exchange okx      # Загрузка данных с OKX
```

### Программное использование

```python
from backtester import Backtester
from reporter import BacktestReporter

# Создание и запуск бэктестера
config = {
    "start_balance": 1000,
    "order_type": "long",
    "dca": {"enabled": True, "max_orders": 3},
    "take_profit": 5,
    "stop_loss": 10,
    "data_file": "data/BTCUSDT_15m.csv"
}

backtester = Backtester(config_dict=config)
results = backtester.run_backtest()

# Создание отчета
reporter = BacktestReporter(results)
print(reporter.generate_summary_report())
reporter.generate_full_report()
```

## 📈 Стратегии

### Long Strategy
- Вход при падении цены на заданный процент от недавнего максимума
- DCA при дальнейшем падении цены
- Выход по Take Profit или Stop Loss от средней цены

### Short Strategy  
- Вход при росте цены на заданный процент от недавнего минимума
- DCA при дальнейшем росте цены
- Выход по Take Profit или Stop Loss от средней цены

### DCA (Dollar Cost Averaging)
- Автоматическое усреднение позиции при неблагоприятном движении
- Настраиваемый шаг и максимальное количество ордеров
- Поддержка стратегии Мартингейл (увеличение размера ордеров)

## 📊 Отчеты и аналитика

Система генерирует следующие отчеты:

### Текстовые отчеты
- Сводный отчет с основными метриками
- Детальный список всех сделок
- Анализ производительности по времени

### Графики (при наличии matplotlib)
- Кривая эквити (изменение баланса)
- Распределение прибылей/убытков
- График просадки
- Месячная доходность

### Метрики
- **Основные**: общая прибыль, доходность, винрейт
- **Риск**: максимальная просадка, Sharpe ratio, VaR
- **Дополнительные**: Profit Factor, Calmar Ratio, Recovery Factor

## 🏗️ Архитектура

Проект состоит из следующих модулей:

- **`data_loader.py`** - загрузка и валидация исторических данных
- **`strategy.py`** - логика торговых стратегий (Long/Short, DCA, Мартингейл)
- **`backtester.py`** - основной движок бэктестирования
- **`reporter.py`** - генерация отчетов и визуализация
- **`main.py`** - CLI интерфейс для запуска
- **`web_app.py`** - веб-интерфейс на Flask
- **`config.json`** - файл конфигурации

## 🐳 Docker архитектура

Проект поддерживает контейнеризацию с помощью Docker:

### Контейнеры:
- **`backtester`** - CLI версия для выполнения бэктестов
- **`backtester-web`** - веб-интерфейс на Flask + Gunicorn
- **`redis`** - кэширование результатов (опционально)

### Файлы Docker:
- **`Dockerfile`** - образ для CLI версии
- **`Dockerfile.web`** - образ для веб-интерфейса
- **`docker-compose.yml`** - оркестрация сервисов
- **`docker-run.sh`** - удобный скрипт управления

### Преимущества Docker:
- ✅ **Изолированная среда** - нет конфликтов зависимостей
- ✅ **Простое развертывание** - один скрипт для запуска
- ✅ **Масштабируемость** - легко добавить воркеры
- ✅ **Портативность** - работает везде где есть Docker

## 🔧 Расширение функциональности

### Добавление новых индикаторов
```python
# В strategy.py добавьте методы для расчета индикаторов
def calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
    # Реализация RSI
    pass

def should_enter_position(self, current_data, historical_data):
    # Используйте индикаторы в логике входа
    rsi = self.calculate_rsi(historical_data)
    if rsi.iloc[-1] < 30:  # Перепроданность
        return True
```

### Добавление API загрузки данных
```python
# В data_loader.py расширьте метод load_from_api
def load_from_api(self, symbol, timeframe, start_date=None, end_date=None):
    # Реализация загрузки с биржи
    pass
```

## 📝 Примеры конфигураций

### Консервативная Long стратегия
```json
{
  "start_balance": 1000,
  "order_type": "long",
  "entry_conditions": {"trigger": "price_drop", "percent": 3},
  "dca": {"enabled": true, "max_orders": 3, "multiplier": 1, "step_percent": 2},
  "take_profit": 3,
  "stop_loss": 15
}
```

### Агрессивная Мартингейл стратегия
```json
{
  "start_balance": 1000,
  "order_type": "long",
  "entry_conditions": {"trigger": "price_drop", "percent": 1},
  "dca": {"enabled": true, "max_orders": 5, "multiplier": 2.5, "step_percent": 1},
  "take_profit": 2,
  "stop_loss": 20
}
```

### Short стратегия
```json
{
  "start_balance": 1000,
  "order_type": "short",
  "entry_conditions": {"trigger": "price_rise", "percent": 2},
  "dca": {"enabled": true, "max_orders": 4, "multiplier": 1.5, "step_percent": 1.5},
  "take_profit": 4,
  "stop_loss": 12
}
```

## ⚠️ Важные замечания

1. **Это инструмент для бэктестирования**, не для реальной торговли
2. **Исторические результаты не гарантируют будущую прибыль**
3. **Учитывайте комиссии и проскальзывания** при реальной торговле
4. **Тестируйте стратегии на разных периодах** и рынках
5. **Используйте риск-менеджмент** в реальной торговле

## 🤝 Вклад в проект

Приветствуются улучшения и новые функции:
- Новые типы стратегий
- Дополнительные индикаторы
- Улучшения в отчетности
- Оптимизация производительности

## 📄 Лицензия

MIT License - подробности в файле LICENSE

## 🆘 Поддержка

При возникновении проблем:
1. Проверьте формат входных данных
2. Убедитесь в корректности конфигурации
3. Используйте `--verbose` для диагностики
4. Создайте issue с описанием проблемы