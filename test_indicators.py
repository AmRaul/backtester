#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы индикаторов
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from indicators import TechnicalIndicators, IndicatorStrategy

def create_sample_data():
    """Создает образец данных для тестирования"""
    print("Создание образца данных для тестирования...")
    
    # Создаем временные метки (1-часовые интервалы)
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    timestamps = []
    current_time = start_date
    while current_time <= end_date:
        timestamps.append(current_time)
        current_time += timedelta(hours=1)
    
    # Генерируем реалистичные OHLCV данные
    np.random.seed(42)  # Для воспроизводимости
    
    n_points = len(timestamps)
    base_price = 30000  # Начальная цена BTC
    
    # Генерируем случайное блуждание с трендом
    returns = np.random.normal(0.0001, 0.02, n_points)  # Небольшой положительный тренд
    
    # Создаем цены закрытия
    closes = [base_price]
    for i in range(1, n_points):
        new_price = closes[-1] * (1 + returns[i])
        closes.append(max(new_price, 100))  # Минимальная цена 100
    
    # Генерируем OHLV на основе цен закрытия
    data = []
    for i, (timestamp, close) in enumerate(zip(timestamps, closes)):
        if i == 0:
            open_price = close
        else:
            open_price = closes[i-1]
        
        # Генерируем high и low с некоторой волатильностью
        volatility = abs(np.random.normal(0, 0.01))
        high = max(open_price, close) * (1 + volatility)
        low = min(open_price, close) * (1 - volatility)
        
        # Убеждаемся, что OHLC логически корректны
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        # Генерируем объем
        volume = np.random.uniform(10, 1000)
        
        data.append({
            'timestamp': timestamp,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': round(volume, 2)
        })
    
    # Создаем DataFrame
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    
    print(f"Создано {len(data)} записей данных")
    print(f"Период: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
    print(f"Диапазон цен: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
    
    return df

def test_indicators():
    """Тестирует все индикаторы"""
    print("\n" + "="*50)
    print("ТЕСТИРОВАНИЕ ИНДИКАТОРОВ")
    print("="*50)
    
    # Создаем данные
    data = create_sample_data()
    
    # Инициализируем индикаторы
    indicators = TechnicalIndicators()
    strategy = IndicatorStrategy(indicators)
    
    print(f"\nДанные загружены: {len(data)} записей")
    print(f"Последние 5 записей:")
    print(data.tail())
    
    # Тестируем EMA
    print("\n" + "-"*30)
    print("ТЕСТ EMA")
    print("-"*30)
    
    ema_50 = indicators.calculate_ema(data['close'], 50, "ema_50_test")
    ema_200 = indicators.calculate_ema(data['close'], 200, "ema_200_test")
    
    print(f"EMA 50 последние значения: {ema_50.tail().values}")
    print(f"EMA 200 последние значения: {ema_200.tail().values}")
    print(f"Тренд вверх: {ema_50.iloc[-1] > ema_200.iloc[-1]}")
    
    # Тестируем RSI
    print("\n" + "-"*30)
    print("ТЕСТ RSI")
    print("-"*30)
    
    rsi = indicators.calculate_rsi(data['close'], 14, "rsi_14_test")
    
    print(f"RSI последние значения: {rsi.tail().values}")
    print(f"Текущий RSI: {rsi.iloc[-1]:.2f}")
    print(f"Перепроданность (RSI < 30): {rsi.iloc[-1] < 30}")
    print(f"Перекупленность (RSI > 70): {rsi.iloc[-1] > 70}")
    
    # Тестируем Bollinger Bands
    print("\n" + "-"*30)
    print("ТЕСТ BOLLINGER BANDS")
    print("-"*30)
    
    bb_upper, bb_middle, bb_lower = indicators.calculate_bollinger_bands(
        data['close'], 20, 2, "bb_20_2_test"
    )
    
    current_price = data['close'].iloc[-1]
    print(f"Текущая цена: {current_price:.2f}")
    print(f"BB Upper: {bb_upper.iloc[-1]:.2f}")
    print(f"BB Middle: {bb_middle.iloc[-1]:.2f}")
    print(f"BB Lower: {bb_lower.iloc[-1]:.2f}")
    print(f"Касание нижней полосы: {current_price <= bb_lower.iloc[-1] * 1.01}")
    print(f"Касание верхней полосы: {current_price >= bb_upper.iloc[-1] * 0.99}")
    
    # Тестируем ATR
    print("\n" + "-"*30)
    print("ТЕСТ ATR")
    print("-"*30)
    
    atr = indicators.calculate_atr(data['high'], data['low'], data['close'], 14, "atr_14_test")
    
    print(f"ATR последние значения: {atr.tail().values}")
    print(f"Текущий ATR: {atr.iloc[-1]:.2f}")
    print(f"ATR как % от цены: {(atr.iloc[-1] / current_price) * 100:.2f}%")
    
    # Тестируем SuperTrend
    print("\n" + "-"*30)
    print("ТЕСТ SUPERTREND")
    print("-"*30)
    
    supertrend, direction = indicators.calculate_supertrend(
        data['high'], data['low'], data['close'], 10, 3, "supertrend_10_3_test"
    )
    
    print(f"SuperTrend последние значения: {supertrend.tail().values}")
    print(f"Direction последние значения: {direction.tail().values}")
    print(f"Текущий SuperTrend: {supertrend.iloc[-1]:.2f}")
    print(f"Текущее направление: {direction.iloc[-1]} (1=long, -1=short)")
    
    # Тестируем Stochastic RSI
    print("\n" + "-"*30)
    print("ТЕСТ STOCHASTIC RSI")
    print("-"*30)
    
    stoch_k, stoch_d = indicators.calculate_stochastic_rsi(
        data['close'], 14, 3, 14, "stoch_rsi_14_3_test"
    )
    
    print(f"Stoch %K последние значения: {stoch_k.tail().values}")
    print(f"Stoch %D последние значения: {stoch_d.tail().values}")
    print(f"Текущий %K: {stoch_k.iloc[-1]:.2f}")
    print(f"Текущий %D: {stoch_d.iloc[-1]:.2f}")
    print(f"Перепроданность (%K < 20): {stoch_k.iloc[-1] < 20}")
    print(f"Перекупленность (%K > 80): {stoch_k.iloc[-1] > 80}")
    
    # Тестируем стратегии
    print("\n" + "="*50)
    print("ТЕСТИРОВАНИЕ СТРАТЕГИЙ")
    print("="*50)
    
    # Конфигурации для тестирования
    trend_momentum_config = {
        'ema_short': 50,
        'ema_long': 200,
        'rsi_period': 14,
        'rsi_oversold': 30,
        'rsi_overbought': 70
    }
    
    volatility_bounce_config = {
        'bb_period': 20,
        'bb_std': 2,
        'atr_period': 14,
        'atr_multiplier': 1.5
    }
    
    momentum_trend_config = {
        'supertrend_period': 10,
        'supertrend_multiplier': 3,
        'stoch_rsi_k': 14,
        'stoch_rsi_d': 3,
        'stoch_rsi_rsi_period': 14
    }
    
    # Тест стратегии "Тренд + импульс"
    print("\n" + "-"*30)
    print("СТРАТЕГИЯ: Тренд + импульс (EMA + RSI)")
    print("-"*30)
    
    trend_signal = strategy.trend_momentum_signal(data, trend_momentum_config)
    print(f"Long сигнал: {trend_signal['long_signal']}")
    print(f"Short сигнал: {trend_signal['short_signal']}")
    print(f"Тренд вверх: {trend_signal['trend_up']}")
    print(f"Тренд вниз: {trend_signal['trend_down']}")
    print(f"RSI перепродан: {trend_signal['rsi_oversold']}")
    print(f"RSI перекуплен: {trend_signal['rsi_overbought']}")
    
    # Тест стратегии "Волатильность + отскок"
    print("\n" + "-"*30)
    print("СТРАТЕГИЯ: Волатильность + отскок (BB + ATR)")
    print("-"*30)
    
    volatility_signal = strategy.volatility_bounce_signal(data, volatility_bounce_config)
    print(f"Long сигнал: {volatility_signal['long_signal']}")
    print(f"Short сигнал: {volatility_signal['short_signal']}")
    print(f"Касание нижней полосы: {volatility_signal['touching_lower']}")
    print(f"Касание верхней полосы: {volatility_signal['touching_upper']}")
    print(f"Низкая волатильность: {volatility_signal['low_volatility']}")
    
    # Тест стратегии "Моментум + трендовый фильтр"
    print("\n" + "-"*30)
    print("СТРАТЕГИЯ: Моментум + трендовый фильтр (SuperTrend + Stoch RSI)")
    print("-"*30)
    
    momentum_signal = strategy.momentum_trend_signal(data, momentum_trend_config)
    print(f"Long сигнал: {momentum_signal['long_signal']}")
    print(f"Short сигнал: {momentum_signal['short_signal']}")
    print(f"Тренд вверх: {momentum_signal['trend_up']}")
    print(f"Тренд вниз: {momentum_signal['trend_down']}")
    print(f"Stoch RSI перепродан: {momentum_signal['stoch_oversold']}")
    print(f"Stoch RSI перекуплен: {momentum_signal['stoch_overbought']}")
    
    # Проверяем кэш
    print("\n" + "-"*30)
    print("ПРОВЕРКА КЭША")
    print("-"*30)
    
    cached_indicators = indicators.get_cached_indicators()
    print(f"Закэшированные индикаторы: {cached_indicators}")
    
    print("\n" + "="*50)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*50)

if __name__ == "__main__":
    test_indicators()
