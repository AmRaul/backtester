#!/usr/bin/env python3
"""
Отладка бэктеста с индикаторами - показывает почему не генерируются сигналы
"""

from backtester import Backtester
from indicators import TechnicalIndicators, IndicatorStrategy
import pandas as pd

# Создаем бэктестер
bt = Backtester(config_path='test_config_indicators.json')

# Загружаем данные
data = bt.load_data()
print(f"\nЗагружено {len(data)} свечей")
print(f"Период: {data['timestamp'].min()} - {data['timestamp'].max()}")

# Создаем индикаторы
indicators = TechnicalIndicators()
indicator_strategy = IndicatorStrategy(indicators)

# Конфиг индикаторов
config = bt.config['indicators']['trend_momentum']
print(f"\nКонфигурация индикаторов:")
print(f"  EMA Short: {config['ema_short']}")
print(f"  EMA Long: {config['ema_long']}")
print(f"  RSI Period: {config['rsi_period']}")

# Минимальный период для анализа
lookback = 200

print(f"\n{'='*80}")
print("Проверяем первые 5 итераций после lookback периода")
print(f"{'='*80}\n")

# Проверяем несколько итераций
for i in range(lookback, min(lookback + 10, len(data))):
    current_data = data.iloc[i]
    historical_data = data.iloc[:i+1]

    # Вызываем индикаторную стратегию точно так же как в реальном бэктесте
    signal_data = indicator_strategy.trend_momentum_signal(historical_data, config)

    print(f"Итерация {i-lookback+1} (индекс {i}):")
    print(f"  Timestamp: {current_data['timestamp']}")
    print(f"  Цена: ${current_data['close']:.4f}")
    print(f"  EMA50: {signal_data['indicators']['ema_50']:.4f}")
    print(f"  EMA200: {signal_data['indicators']['ema_200']:.4f}")
    print(f"  RSI: {signal_data['indicators']['rsi']:.2f}")
    print(f"  Тренд вверх: {signal_data['trend_up']}")
    print(f"  Тренд вниз: {signal_data['trend_down']}")
    print(f"  RSI перепродан (<40): {signal_data['indicators']['rsi'] < 40}")
    print(f"  🎯 LONG сигнал: {signal_data['long_signal']}")
    print(f"  🎯 SHORT сигнал: {signal_data['short_signal']}")

    if signal_data['long_signal']:
        print(f"  ✅ Найден LONG сигнал!")

    print()

# Ищем первый сигнал во всем датасете
print(f"\n{'='*80}")
print("Поиск первого LONG сигнала во всем датасете...")
print(f"{'='*80}\n")

signal_found = False
for i in range(lookback, len(data)):
    historical_data = data.iloc[:i+1]
    signal_data = indicator_strategy.trend_momentum_signal(historical_data, config)

    if signal_data['long_signal']:
        current_data = data.iloc[i]
        print(f"✅ Первый LONG сигнал найден!")
        print(f"  Итерация: {i-lookback+1} (индекс {i})")
        print(f"  Timestamp: {current_data['timestamp']}")
        print(f"  Цена: ${current_data['close']:.4f}")
        print(f"  EMA50: {signal_data['indicators']['ema_50']:.4f}")
        print(f"  EMA200: {signal_data['indicators']['ema_200']:.4f}")
        print(f"  RSI: {signal_data['indicators']['rsi']:.2f}")
        signal_found = True
        break

if not signal_found:
    print("❌ LONG сигналов не найдено во всем датасете!")
    print("\nВозможные причины:")
    print("1. Никогда не было одновременно: тренд вверх (EMA50 > EMA200) И RSI < 40")
    print("2. Проблема с данными или индикаторами")
