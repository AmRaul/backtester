"""
Тесты для модуля indicators.py
Покрывает классы TechnicalIndicators и IndicatorStrategy
"""

import pytest
import pandas as pd
import numpy as np
from indicators import TechnicalIndicators, IndicatorStrategy


class TestTechnicalIndicators:
    """Тесты для класса TechnicalIndicators"""
    
    @pytest.fixture
    def sample_data(self):
        """Создает образец данных OHLCV для тестирования"""
        dates = pd.date_range('2023-01-01', periods=300, freq='15min')
        np.random.seed(42)
        base_price = 30000
        prices = base_price + np.cumsum(np.random.randn(300) * 100)
        
        return pd.DataFrame({
            'open': prices + np.random.randn(300) * 50,
            'high': prices + np.abs(np.random.randn(300) * 100),
            'low': prices - np.abs(np.random.randn(300) * 100),
            'close': prices,
            'volume': np.random.randint(1000, 10000, 300)
        }, index=dates)
    
    @pytest.fixture
    def indicators(self):
        """Создает экземпляр TechnicalIndicators"""
        return TechnicalIndicators()
    
    def test_ema_calculation(self, indicators, sample_data):
        """Тест расчета EMA"""
        ema = indicators.calculate_ema(sample_data['close'], period=50)
        
        assert isinstance(ema, pd.Series)
        assert len(ema) == len(sample_data)
        assert not ema.iloc[0:49].notna().all()  # Первые значения должны быть NaN
        assert ema.iloc[49:].notna().all()  # После периода должны быть значения
        
        # EMA должна быть сглаженной версией цены
        assert ema.iloc[-1] > 0
    
    def test_ema_caching(self, indicators, sample_data):
        """Тест кэширования EMA"""
        cache_key = 'test_ema_50'
        
        ema1 = indicators.calculate_ema(sample_data['close'], period=50, cache_key=cache_key)
        ema2 = indicators.calculate_ema(sample_data['close'], period=50, cache_key=cache_key)
        
        pd.testing.assert_series_equal(ema1, ema2)
        assert cache_key in indicators.get_cached_indicators()
    
    def test_rsi_calculation(self, indicators, sample_data):
        """Тест расчета RSI"""
        rsi = indicators.calculate_rsi(sample_data['close'], period=14)
        
        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(sample_data)
        assert not rsi.iloc[0:13].notna().all()  # Первые значения должны быть NaN
        assert rsi.iloc[13:].notna().all()
        
        # RSI должен быть в диапазоне 0-100
        assert (rsi.iloc[13:] >= 0).all()
        assert (rsi.iloc[13:] <= 100).all()
    
    def test_bollinger_bands_calculation(self, indicators, sample_data):
        """Тест расчета Bollinger Bands"""
        upper, middle, lower = indicators.calculate_bollinger_bands(
            sample_data['close'], period=20, std_dev=2
        )
        
        assert isinstance(upper, pd.Series)
        assert isinstance(middle, pd.Series)
        assert isinstance(lower, pd.Series)
        assert len(upper) == len(sample_data)
        
        # Верхняя полоса должна быть выше средней, а средняя выше нижней
        valid_idx = ~(upper.isna() | middle.isna() | lower.isna())
        assert (upper[valid_idx] >= middle[valid_idx]).all()
        assert (middle[valid_idx] >= lower[valid_idx]).all()
    
    def test_atr_calculation(self, indicators, sample_data):
        """Тест расчета ATR"""
        atr = indicators.calculate_atr(
            sample_data['high'], sample_data['low'], sample_data['close'], period=14
        )
        
        assert isinstance(atr, pd.Series)
        assert len(atr) == len(sample_data)
        assert not atr.iloc[0:13].notna().all()  # Первые значения должны быть NaN
        assert atr.iloc[13:].notna().all()
        
        # ATR должен быть положительным
        assert (atr.iloc[13:] > 0).all()
    
    def test_macd_calculation(self, indicators, sample_data):
        """Тест расчета MACD"""
        macd_line, signal_line, histogram = indicators.calculate_macd(
            sample_data['close'], fast_period=12, slow_period=26, signal_period=9
        )
        
        assert isinstance(macd_line, pd.Series)
        assert isinstance(signal_line, pd.Series)
        assert isinstance(histogram, pd.Series)
        assert len(macd_line) == len(sample_data)
        
        # Гистограмма должна быть разницей между MACD и сигнальной линией
        valid_idx = ~(macd_line.isna() | signal_line.isna() | histogram.isna())
        expected_histogram = macd_line[valid_idx] - signal_line[valid_idx]
        pd.testing.assert_series_equal(histogram[valid_idx], expected_histogram, rtol=1e-5)
    
    def test_supertrend_calculation(self, indicators, sample_data):
        """Тест расчета SuperTrend"""
        supertrend, direction = indicators.calculate_supertrend(
            sample_data['high'], sample_data['low'], sample_data['close'],
            period=10, multiplier=3
        )
        
        assert isinstance(supertrend, pd.Series)
        assert isinstance(direction, pd.Series)
        assert len(supertrend) == len(sample_data)
        assert len(direction) == len(sample_data)
        
        # Направление должно быть либо 1, либо -1
        valid_idx = ~direction.isna()
        assert direction[valid_idx].isin([1, -1]).all()
        assert (supertrend[valid_idx] > 0).all()
    
    def test_stochastic_rsi_calculation(self, indicators, sample_data):
        """Тест расчета Stochastic RSI"""
        k_percent, d_percent = indicators.calculate_stochastic_rsi(
            sample_data['close'], k_period=14, d_period=3, rsi_period=14
        )
        
        assert isinstance(k_percent, pd.Series)
        assert isinstance(d_percent, pd.Series)
        assert len(k_percent) == len(sample_data)
        
        # Значения должны быть в диапазоне 0-1 (или 0-100)
        valid_idx = ~k_percent.isna()
        if valid_idx.any():
            # Проверяем, что значения в разумном диапазоне
            assert (k_percent[valid_idx] >= -10).all()  # Допускаем небольшие отрицательные из-за округлений
            assert (k_percent[valid_idx] <= 110).all()  # Допускаем небольшие превышения из-за округлений
    
    def test_cache_operations(self, indicators, sample_data):
        """Тест операций с кэшем"""
        cache_key = 'test_cache'
        
        # Добавляем значение в кэш
        indicators.calculate_ema(sample_data['close'], period=50, cache_key=cache_key)
        assert cache_key in indicators.get_cached_indicators()
        
        # Очищаем кэш
        indicators.clear_cache()
        assert len(indicators.get_cached_indicators()) == 0


class TestIndicatorStrategy:
    """Тесты для класса IndicatorStrategy"""
    
    @pytest.fixture
    def sample_data(self):
        """Создает образец данных OHLCV для тестирования"""
        dates = pd.date_range('2023-01-01', periods=300, freq='15min')
        np.random.seed(42)
        base_price = 30000
        prices = base_price + np.cumsum(np.random.randn(300) * 100)
        
        return pd.DataFrame({
            'open': prices + np.random.randn(300) * 50,
            'high': prices + np.abs(np.random.randn(300) * 100),
            'low': prices - np.abs(np.random.randn(300) * 100),
            'close': prices,
            'volume': np.random.randint(1000, 10000, 300)
        }, index=dates)
    
    @pytest.fixture
    def strategy(self):
        """Создает экземпляр IndicatorStrategy"""
        indicators = TechnicalIndicators()
        return IndicatorStrategy(indicators)
    
    def test_trend_momentum_signal_structure(self, strategy, sample_data):
        """Тест структуры результата trend_momentum_signal"""
        config = {
            'ema_short': 50,
            'ema_long': 200,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70
        }
        
        result = strategy.trend_momentum_signal(sample_data, config)
        
        assert isinstance(result, dict)
        assert 'long_signal' in result
        assert 'short_signal' in result
        assert 'trend_up' in result
        assert 'trend_down' in result
        assert 'rsi_oversold' in result
        assert 'rsi_overbought' in result
        assert 'indicators' in result
        
        assert isinstance(result['long_signal'], bool)
        assert isinstance(result['short_signal'], bool)
        assert isinstance(result['indicators'], dict)
    
    def test_trend_momentum_signal_indicators(self, strategy, sample_data):
        """Тест наличия индикаторов в результате trend_momentum_signal"""
        config = {
            'ema_short': 50,
            'ema_long': 200,
            'rsi_period': 14
        }
        
        result = strategy.trend_momentum_signal(sample_data, config)
        indicators = result['indicators']
        
        assert 'ema_50' in indicators
        assert 'ema_200' in indicators
        assert 'rsi' in indicators
        assert 'ema_50_series' in indicators
        assert 'ema_200_series' in indicators
        assert 'rsi_series' in indicators
    
    def test_volatility_bounce_signal_structure(self, strategy, sample_data):
        """Тест структуры результата volatility_bounce_signal"""
        config = {
            'bb_period': 20,
            'bb_std': 2,
            'atr_period': 14
        }
        
        result = strategy.volatility_bounce_signal(sample_data, config)
        
        assert isinstance(result, dict)
        assert 'long_signal' in result
        assert 'short_signal' in result
        assert 'touching_lower' in result
        assert 'touching_upper' in result
        assert 'low_volatility' in result
        assert 'indicators' in result
    
    def test_momentum_trend_signal_structure(self, strategy, sample_data):
        """Тест структуры результата momentum_trend_signal"""
        config = {
            'supertrend_period': 10,
            'supertrend_multiplier': 3,
            'stoch_rsi_k': 14,
            'stoch_rsi_d': 3
        }
        
        result = strategy.momentum_trend_signal(sample_data, config)
        
        assert isinstance(result, dict)
        assert 'long_signal' in result
        assert 'short_signal' in result
        assert 'trend_up' in result
        assert 'trend_down' in result
        assert 'stoch_oversold' in result
        assert 'stoch_overbought' in result
        assert 'indicators' in result
    
    def test_custom_signal_structure(self, strategy, sample_data):
        """Тест структуры результата custom_signal"""
        config = {
            'selected_indicators': {
                'ema': True,
                'rsi': True
            },
            'ema': {
                'short_period': 50,
                'long_period': 200
            },
            'rsi': {
                'period': 14,
                'oversold': 30,
                'overbought': 70
            }
        }
        
        result = strategy.custom_signal(sample_data, config)
        
        assert isinstance(result, dict)
        assert 'long_signal' in result
        assert 'short_signal' in result
        assert 'indicators' in result
        assert isinstance(result['long_signal'], bool)
        assert isinstance(result['short_signal'], bool)
    
    def test_custom_signal_no_indicators(self, strategy, sample_data):
        """Тест custom_signal с пустыми индикаторами"""
        config = {
            'selected_indicators': {}
        }
        
        result = strategy.custom_signal(sample_data, config)
        
        assert result['long_signal'] == False
        assert result['short_signal'] == False
    
    def test_empty_data_handling(self, strategy):
        """Тест обработки пустых данных"""
        empty_data = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
        config = {'ema_short': 50, 'ema_long': 200}
        
        result = strategy.trend_momentum_signal(empty_data, config)
        
        assert result['long_signal'] == False
        assert result['short_signal'] == False
        assert isinstance(result['indicators'], dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

