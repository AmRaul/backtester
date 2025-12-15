"""
Модуль для расчета технических индикаторов
Использует библиотеку ta для быстрых и точных вычислений
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import ta

class TechnicalIndicators:
    """
    Класс для расчета технических индикаторов
    Использует библиотеку ta для оптимизированных вычислений
    """
    
    def __init__(self):
        self.cache = {}  # Кэш для хранения вычисленных индикаторов
    
    def calculate_ema(self, data: pd.Series, period: int, cache_key: str = None) -> pd.Series:
        """
        Вычисляет Exponential Moving Average (EMA)
        
        Args:
            data: серия цен (обычно close)
            period: период EMA
            cache_key: ключ для кэширования (опционально)
            
        Returns:
            pd.Series с EMA значениями
        """
        if cache_key and cache_key in self.cache:
            return self.cache[cache_key]
        
        ema = ta.trend.EMAIndicator(close=data, window=period).ema_indicator()
        
        if cache_key:
            self.cache[cache_key] = ema
            
        return ema
    
    def calculate_rsi(self, data: pd.Series, period: int = 14, cache_key: str = None) -> pd.Series:
        """
        Вычисляет Relative Strength Index (RSI)
        
        Args:
            data: серия цен (обычно close)
            period: период RSI (по умолчанию 14)
            cache_key: ключ для кэширования (опционально)
            
        Returns:
            pd.Series с RSI значениями (0-100)
        """
        if cache_key and cache_key in self.cache:
            return self.cache[cache_key]
        
        rsi = ta.momentum.RSIIndicator(close=data, window=period).rsi()
        
        if cache_key:
            self.cache[cache_key] = rsi
            
        return rsi
    
    def calculate_bollinger_bands(self, data: pd.Series, period: int = 20, 
                                std_dev: float = 2, cache_key: str = None) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Вычисляет Bollinger Bands
        
        Args:
            data: серия цен (обычно close)
            period: период для SMA
            std_dev: количество стандартных отклонений
            cache_key: ключ для кэширования (опционально)
            
        Returns:
            Tuple (upper_band, middle_band, lower_band)
        """
        if cache_key and cache_key in self.cache:
            return self.cache[cache_key]
        
        bb = ta.volatility.BollingerBands(close=data, window=period, window_dev=std_dev)
        upper = bb.bollinger_hband()
        middle = bb.bollinger_mavg()
        lower = bb.bollinger_lband()
        
        result = (upper, middle, lower)
        
        if cache_key:
            self.cache[cache_key] = result
            
        return result
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                     period: int = 14, cache_key: str = None) -> pd.Series:
        """
        Вычисляет Average True Range (ATR)
        
        Args:
            high: серия максимальных цен
            low: серия минимальных цен
            close: серия цен закрытия
            period: период ATR
            cache_key: ключ для кэширования (опционально)
            
        Returns:
            pd.Series с ATR значениями
        """
        if cache_key and cache_key in self.cache:
            return self.cache[cache_key]
        
        atr = ta.volatility.AverageTrueRange(high=high, low=low, close=close, window=period).average_true_range()
        
        if cache_key:
            self.cache[cache_key] = atr
            
        return atr
    
    def calculate_supertrend(self, high: pd.Series, low: pd.Series, close: pd.Series,
                           period: int = 10, multiplier: float = 3, cache_key: str = None) -> Tuple[pd.Series, pd.Series]:
        """
        Вычисляет SuperTrend индикатор

        Args:
            high: серия максимальных цен
            low: серия минимальных цен
            close: серия цен закрытия
            period: период ATR для SuperTrend
            multiplier: множитель ATR
            cache_key: ключ для кэширования (опционально)

        Returns:
            Tuple (supertrend_line, direction)
        """
        if cache_key and cache_key in self.cache:
            return self.cache[cache_key]

        # Реализуем SuperTrend вручную
        # Вычисляем ATR
        atr = ta.volatility.AverageTrueRange(high=high, low=low, close=close, window=period).average_true_range()

        # Вычисляем базовые полосы
        hl2 = (high + low) / 2
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)

        # Инициализируем массивы
        supertrend_line = pd.Series(index=close.index, dtype=float)
        direction = pd.Series(index=close.index, dtype=float)

        # Первое значение
        supertrend_line.iloc[0] = upper_band.iloc[0]
        direction.iloc[0] = 1

        # Вычисляем SuperTrend
        for i in range(1, len(close)):
            # Определяем направление тренда
            if close.iloc[i] > supertrend_line.iloc[i-1]:
                direction.iloc[i] = 1  # Восходящий тренд
                supertrend_line.iloc[i] = lower_band.iloc[i] if lower_band.iloc[i] > supertrend_line.iloc[i-1] else supertrend_line.iloc[i-1]
            else:
                direction.iloc[i] = -1  # Нисходящий тренд
                supertrend_line.iloc[i] = upper_band.iloc[i] if upper_band.iloc[i] < supertrend_line.iloc[i-1] else supertrend_line.iloc[i-1]

        result = (supertrend_line, direction)
        
        if cache_key:
            self.cache[cache_key] = result
            
        return result
    
    def calculate_stochastic_rsi(self, data: pd.Series, k_period: int = 14, d_period: int = 3,
                               rsi_period: int = 14, cache_key: str = None) -> Tuple[pd.Series, pd.Series]:
        """
        Вычисляет Stochastic RSI
        
        Args:
            data: серия цен (обычно close)
            k_period: период %K
            d_period: период %D
            rsi_period: период RSI
            cache_key: ключ для кэширования (опционально)
            
        Returns:
            Tuple (%K, %D)
        """
        if cache_key and cache_key in self.cache:
            return self.cache[cache_key]
        
        stoch_rsi = ta.momentum.StochRSIIndicator(
            close=data, window=k_period, smooth1=d_period, smooth2=d_period
        )
        
        k_percent = stoch_rsi.stochrsi_k()
        d_percent = stoch_rsi.stochrsi_d()
        
        result = (k_percent, d_percent)
        
        if cache_key:
            self.cache[cache_key] = result
            
        return result
    
    def calculate_macd(self, data: pd.Series, fast_period: int = 12, slow_period: int = 26,
                      signal_period: int = 9, cache_key: str = None) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Вычисляет MACD (Moving Average Convergence Divergence)
        
        Args:
            data: серия цен (обычно close)
            fast_period: период быстрой EMA
            slow_period: период медленной EMA
            signal_period: период сигнальной линии
            cache_key: ключ для кэширования (опционально)
            
        Returns:
            Tuple (macd_line, signal_line, histogram)
        """
        if cache_key and cache_key in self.cache:
            return self.cache[cache_key]
        
        macd = ta.trend.MACD(
            close=data, window_fast=fast_period, window_slow=slow_period, window_sign=signal_period
        )
        
        macd_line = macd.macd()
        signal_line = macd.macd_signal()
        histogram = macd.macd_diff()
        
        result = (macd_line, signal_line, histogram)
        
        if cache_key:
            self.cache[cache_key] = result
            
        return result
    
    def clear_cache(self):
        """Очищает кэш индикаторов"""
        self.cache.clear()
    
    def get_cached_indicators(self) -> List[str]:
        """Возвращает список закэшированных индикаторов"""
        return list(self.cache.keys())


class IndicatorStrategy:
    """
    Класс для работы со стратегиями на основе индикаторов
    """
    
    def __init__(self, indicators: TechnicalIndicators):
        self.indicators = indicators
    
    def trend_momentum_signal(self, data: pd.DataFrame, config: dict) -> dict:
        """
        Стратегия: Тренд + импульс (EMA + RSI)
        
        Args:
            data: DataFrame с OHLCV данными
            config: конфигурация стратегии
            
        Returns:
            dict с сигналами и значениями индикаторов
        """
        # Получаем параметры
        ema_short = config.get('ema_short', 50)
        ema_long = config.get('ema_long', 200)
        rsi_period = config.get('rsi_period', 14)
        rsi_oversold = config.get('rsi_oversold', 30)
        rsi_overbought = config.get('rsi_overbought', 70)
        
        # Вычисляем индикаторы (БЕЗ кэширования для корректной работы в бэктесте)
        ema_50 = self.indicators.calculate_ema(
            data['close'], ema_short, cache_key=None
        )
        ema_200 = self.indicators.calculate_ema(
            data['close'], ema_long, cache_key=None
        )
        rsi = self.indicators.calculate_rsi(
            data['close'], rsi_period, cache_key=None
        )
        
        # Получаем текущие значения (используем -1 для последнего элемента)
        if len(data) == 0 or len(ema_50) == 0 or len(ema_200) == 0 or len(rsi) == 0:
            return {
                'long_signal': False,
                'short_signal': False,
                'trend_up': False,
                'trend_down': False,
                'rsi_oversold': False,
                'rsi_overbought': False,
                'indicators': {
                    'ema_50': 0,
                    'ema_200': 0,
                    'rsi': 0,
                    'ema_50_series': ema_50,
                    'ema_200_series': ema_200,
                    'rsi_series': rsi
                }
            }

        # Проверяем, что у нас достаточно данных
        if pd.isna(ema_50.iloc[-1]) or pd.isna(ema_200.iloc[-1]) or pd.isna(rsi.iloc[-1]):
            return {
                'long_signal': False,
                'short_signal': False,
                'trend_up': False,
                'trend_down': False,
                'rsi_oversold': False,
                'rsi_overbought': False,
                'indicators': {
                    'ema_50': 0,
                    'ema_200': 0,
                    'rsi': 0,
                    'ema_50_series': ema_50,
                    'ema_200_series': ema_200,
                    'rsi_series': rsi
                }
            }

        ema_50_current = ema_50.iloc[-1]
        ema_200_current = ema_200.iloc[-1]
        rsi_current = rsi.iloc[-1]
        
        # Определяем тренд
        trend_up = ema_50_current > ema_200_current
        trend_down = ema_50_current < ema_200_current
        
        # Определяем сигналы (более мягкие условия)
        long_signal = trend_up and rsi_current < 40  # Мягче чем 30
        short_signal = trend_down and rsi_current > 60  # Мягче чем 70
        
        # Отладочная информация (закомментирована чтобы не спамить)
        # print(f"DEBUG: EMA50={ema_50_current:.2f}, EMA200={ema_200_current:.2f}, RSI={rsi_current:.2f}")
        # print(f"DEBUG: trend_up={trend_up}, trend_down={trend_down}")
        # print(f"DEBUG: long_signal={long_signal}, short_signal={short_signal}")
        
        return {
            'long_signal': long_signal,
            'short_signal': short_signal,
            'trend_up': trend_up,
            'trend_down': trend_down,
            'rsi_oversold': rsi_current < rsi_oversold,
            'rsi_overbought': rsi_current > rsi_overbought,
            'indicators': {
                'ema_50': ema_50_current,
                'ema_200': ema_200_current,
                'rsi': rsi_current,
                'ema_50_series': ema_50,
                'ema_200_series': ema_200,
                'rsi_series': rsi
            }
        }
    
    def volatility_bounce_signal(self, data: pd.DataFrame, config: dict) -> dict:
        """
        Стратегия: Волатильность + отскок (Bollinger Bands + ATR)
        
        Args:
            data: DataFrame с OHLCV данными
            config: конфигурация стратегии
            
        Returns:
            dict с сигналами и значениями индикаторов
        """
        # Получаем параметры
        bb_period = config.get('bb_period', 20)
        bb_std = config.get('bb_std', 2)
        atr_period = config.get('atr_period', 14)
        
        # Вычисляем индикаторы (БЕЗ кэширования для корректной работы в бэктесте)
        bb_upper, bb_middle, bb_lower = self.indicators.calculate_bollinger_bands(
            data['close'], bb_period, bb_std, cache_key=None
        )
        atr = self.indicators.calculate_atr(
            data['high'], data['low'], data['close'], atr_period, cache_key=None
        )
        
        # Получаем текущие значения (используем -1 для последнего элемента)
        if (len(data) == 0 or len(bb_upper) == 0 or len(bb_lower) == 0 or len(atr) == 0):
            return {
                'long_signal': False,
                'short_signal': False,
                'touching_lower': False,
                'touching_upper': False,
                'low_volatility': False,
                'indicators': {
                    'bb_upper': 0,
                    'bb_middle': 0,
                    'bb_lower': 0,
                    'atr': 0,
                    'avg_atr': 0,
                    'bb_upper_series': bb_upper,
                    'bb_middle_series': bb_middle,
                    'bb_lower_series': bb_lower,
                    'atr_series': atr
                }
            }

        # Проверяем, что у нас достаточно данных
        if (pd.isna(bb_upper.iloc[-1]) or
            pd.isna(bb_lower.iloc[-1]) or
            pd.isna(atr.iloc[-1])):
            return {
                'long_signal': False,
                'short_signal': False,
                'touching_lower': False,
                'touching_upper': False,
                'low_volatility': False,
                'indicators': {
                    'bb_upper': 0,
                    'bb_middle': 0,
                    'bb_lower': 0,
                    'atr': 0,
                    'avg_atr': 0,
                    'bb_upper_series': bb_upper,
                    'bb_middle_series': bb_middle,
                    'bb_lower_series': bb_lower,
                    'atr_series': atr
                }
            }

        current_price = data['close'].iloc[-1]
        bb_upper_current = bb_upper.iloc[-1]
        bb_lower_current = bb_lower.iloc[-1]
        atr_current = atr.iloc[-1]
        
        # Проверяем касание полос
        touching_lower = current_price <= bb_lower_current * 1.01  # 1% допуск
        touching_upper = current_price >= bb_upper_current * 0.99  # 1% допуск
        
        # Проверяем низкую волатильность (ATR ниже среднего)
        avg_atr = atr.tail(20).mean()
        low_volatility = atr_current < avg_atr * 0.8
        
        # Определяем сигналы
        long_signal = touching_lower and low_volatility
        short_signal = touching_upper and low_volatility
        
        return {
            'long_signal': long_signal,
            'short_signal': short_signal,
            'touching_lower': touching_lower,
            'touching_upper': touching_upper,
            'low_volatility': low_volatility,
            'indicators': {
                'bb_upper': bb_upper_current,
                'bb_middle': bb_middle.iloc[-1],
                'bb_lower': bb_lower_current,
                'atr': atr_current,
                'avg_atr': avg_atr,
                'bb_upper_series': bb_upper,
                'bb_middle_series': bb_middle,
                'bb_lower_series': bb_lower,
                'atr_series': atr
            }
        }
    
    def momentum_trend_signal(self, data: pd.DataFrame, config: dict) -> dict:
        """
        Стратегия: Моментум + трендовый фильтр (SuperTrend + Stochastic RSI)
        
        Args:
            data: DataFrame с OHLCV данными
            config: конфигурация стратегии
            
        Returns:
            dict с сигналами и значениями индикаторов
        """
        # Получаем параметры
        st_period = config.get('supertrend_period', 10)
        st_mult = config.get('supertrend_multiplier', 3)
        stoch_k = config.get('stoch_rsi_k', 14)
        stoch_d = config.get('stoch_rsi_d', 3)
        
        # Вычисляем индикаторы (БЕЗ кэширования для корректной работы в бэктесте)
        supertrend, direction = self.indicators.calculate_supertrend(
            data['high'], data['low'], data['close'], st_period, st_mult,
            cache_key=None
        )

        stoch_k_percent, stoch_d_percent = self.indicators.calculate_stochastic_rsi(
            data['close'], stoch_k, stoch_d, 14, cache_key=None
        )
        
        # Получаем текущие значения (используем -1 для последнего элемента)
        if (len(data) == 0 or len(direction) == 0 or len(stoch_k_percent) == 0 or len(stoch_d_percent) == 0):
            return {
                'long_signal': False,
                'short_signal': False,
                'trend_up': False,
                'trend_down': False,
                'stoch_oversold': False,
                'stoch_overbought': False,
                'indicators': {
                    'supertrend': 0,
                    'direction': 0,
                    'stoch_k': 0,
                    'stoch_d': 0,
                    'supertrend_series': supertrend,
                    'direction_series': direction,
                    'stoch_k_series': stoch_k_percent,
                    'stoch_d_series': stoch_d_percent
                }
            }

        # Проверяем, что у нас достаточно данных
        if (pd.isna(direction.iloc[-1]) or
            pd.isna(stoch_k_percent.iloc[-1]) or
            pd.isna(stoch_d_percent.iloc[-1])):
            return {
                'long_signal': False,
                'short_signal': False,
                'trend_up': False,
                'trend_down': False,
                'stoch_oversold': False,
                'stoch_overbought': False,
                'indicators': {
                    'supertrend': 0,
                    'direction': 0,
                    'stoch_k': 0,
                    'stoch_d': 0,
                    'supertrend_series': supertrend,
                    'direction_series': direction,
                    'stoch_k_series': stoch_k_percent,
                    'stoch_d_series': stoch_d_percent
                }
            }

        direction_current = direction.iloc[-1]
        stoch_k_current = stoch_k_percent.iloc[-1]
        stoch_d_current = stoch_d_percent.iloc[-1]
        
        # Проверяем направление SuperTrend
        trend_up = direction_current == 1
        trend_down = direction_current == -1
        
        # Проверяем Stochastic RSI
        stoch_oversold = stoch_k_current < 20
        stoch_overbought = stoch_k_current > 80
        
        # Определяем сигналы
        long_signal = trend_up and stoch_oversold
        short_signal = trend_down and stoch_overbought
        
        return {
            'long_signal': long_signal,
            'short_signal': short_signal,
            'trend_up': trend_up,
            'trend_down': trend_down,
            'stoch_oversold': stoch_oversold,
            'stoch_overbought': stoch_overbought,
            'indicators': {
                'supertrend': supertrend.iloc[-1],
                'direction': direction_current,
                'stoch_k': stoch_k_current,
                'stoch_d': stoch_d_current,
                'supertrend_series': supertrend,
                'direction_series': direction,
                'stoch_k_series': stoch_k_percent,
                'stoch_d_series': stoch_d_percent
            }
        }
