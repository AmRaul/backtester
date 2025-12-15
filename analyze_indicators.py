#!/usr/bin/env python3
"""
Анализ значений индикаторов на данных
"""

import pandas as pd
from indicators import TechnicalIndicators

# Загружаем данные
data = pd.read_csv('data/ASTERUSDT:USDT_15m_20251214_045755.csv')
data['timestamp'] = pd.to_datetime(data['timestamp'])
data.set_index('timestamp', inplace=True)

print("\n" + "="*70)
print("АНАЛИЗ ИНДИКАТОРОВ RSI И EMA")
print("="*70 + "\n")

print(f"Всего свечей: {len(data)}")
print(f"Период: {data.index[0]} - {data.index[-1]}")

# Вычисляем индикаторы
indicators = TechnicalIndicators()

ema_50 = indicators.calculate_ema(data['close'], 50)
ema_200 = indicators.calculate_ema(data['close'], 200)
rsi = indicators.calculate_rsi(data['close'], 14)

# Добавляем в DataFrame
data['ema_50'] = ema_50
data['ema_200'] = ema_200
data['rsi'] = rsi

# Определяем тренд и условия
data['trend_up'] = data['ema_50'] > data['ema_200']
data['rsi_low'] = data['rsi'] < 40  # Условие для входа в лонг

# Фильтруем данные где есть все индикаторы (пропускаем первые 200 свечей где нет EMA200)
data_with_indicators = data[200:].copy()

print(f"\nСвечей с полными индикаторами: {len(data_with_indicators)}")

# Статистика по тренду
trend_up_count = data_with_indicators['trend_up'].sum()
trend_down_count = len(data_with_indicators) - trend_up_count

print(f"\n📊 Статистика тренда (EMA50 vs EMA200):")
print(f"   Восходящий тренд (EMA50 > EMA200): {trend_up_count} ({trend_up_count/len(data_with_indicators)*100:.1f}%)")
print(f"   Нисходящий тренд (EMA50 < EMA200): {trend_down_count} ({trend_down_count/len(data_with_indicators)*100:.1f}%)")

# Статистика по RSI
print(f"\n📊 Статистика RSI:")
print(f"   RSI < 30 (перепродан): {(data_with_indicators['rsi'] < 30).sum()} свечей")
print(f"   RSI < 40: {(data_with_indicators['rsi'] < 40).sum()} свечей")
print(f"   RSI < 50: {(data_with_indicators['rsi'] < 50).sum()} свечей")
print(f"   RSI > 70 (перекуплен): {(data_with_indicators['rsi'] > 70).sum()} свечей")
print(f"   Средний RSI: {data_with_indicators['rsi'].mean():.2f}")
print(f"   Мин RSI: {data_with_indicators['rsi'].min():.2f}")
print(f"   Макс RSI: {data_with_indicators['rsi'].max():.2f}")

# Проверяем условия для входа в LONG
data_with_indicators['long_signal_conditions'] = (
    data_with_indicators['trend_up'] &  # Восходящий тренд
    data_with_indicators['rsi_low']      # RSI < 40
)

long_signals = data_with_indicators['long_signal_conditions'].sum()

print(f"\n🎯 Сигналы на вход (LONG):")
print(f"   Тренд вверх И RSI < 40: {long_signals} сигналов")

# Показываем первые 5 сигналов если есть
if long_signals > 0:
    print(f"\n   Первые 5 сигналов:")
    signals_data = data_with_indicators[data_with_indicators['long_signal_conditions']]
    for i, (timestamp, row) in enumerate(signals_data.head(5).iterrows(), 1):
        print(f"      {i}. {timestamp} | Price: ${row['close']:.4f} | EMA50: {row['ema_50']:.4f} | EMA200: {row['ema_200']:.4f} | RSI: {row['rsi']:.2f}")
else:
    print(f"\n   ❌ Сигналов не найдено с текущими условиями")
    print(f"\n   💡 Попробуем смягчить условия:")

    # Проверяем с более мягкими условиями
    data_with_indicators['long_signal_soft'] = (
        data_with_indicators['trend_up'] &
        (data_with_indicators['rsi'] < 50)
    )

    soft_signals = data_with_indicators['long_signal_soft'].sum()
    print(f"      Тренд вверх И RSI < 50: {soft_signals} сигналов")

    if soft_signals > 0:
        print(f"\n   Первые 5 сигналов (мягкие условия):")
        signals_data = data_with_indicators[data_with_indicators['long_signal_soft']]
        for i, (timestamp, row) in enumerate(signals_data.head(5).iterrows(), 1):
            print(f"      {i}. {timestamp} | Price: ${row['close']:.4f} | EMA50: {row['ema_50']:.4f} | EMA200: {row['ema_200']:.4f} | RSI: {row['rsi']:.2f}")

# Последние значения
print(f"\n📌 Последние значения:")
print(f"   Цена: ${data_with_indicators['close'].iloc[-1]:.4f}")
print(f"   EMA50: {data_with_indicators['ema_50'].iloc[-1]:.4f}")
print(f"   EMA200: {data_with_indicators['ema_200'].iloc[-1]:.4f}")
print(f"   RSI: {data_with_indicators['rsi'].iloc[-1]:.2f}")
print(f"   Тренд: {'↗ Восходящий' if data_with_indicators['trend_up'].iloc[-1] else '↘ Нисходящий'}")

print("\n" + "="*70)
print("АНАЛИЗ ЗАВЕРШЕН")
print("="*70 + "\n")
