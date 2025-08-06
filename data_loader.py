import pandas as pd
import numpy as np
from typing import Optional, Union, List
from pathlib import Path
import requests
import json
from datetime import datetime, timedelta
import time

try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    print("CCXT не установлен. Загрузка с бирж недоступна.")

class DataLoader:
    """
    Класс для загрузки исторических данных OHLCV
    Поддерживает загрузку из CSV файлов и API (расширяемо)
    """
    
    def __init__(self):
        self.data = None
        self.symbol = None
        self.timeframe = None
    
    def load_from_csv(self, file_path: Union[str, Path], symbol: str = None) -> pd.DataFrame:
        """
        Загружает данные из CSV файла
        
        Args:
            file_path: путь к CSV файлу
            symbol: символ торговой пары
            
        Returns:
            DataFrame с колонками: timestamp, open, high, low, close, volume
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Файл {file_path} не найден")
            
            # Загружаем CSV
            df = pd.read_csv(file_path)
            
            # Проверяем наличие обязательных колонок
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Отсутствуют обязательные колонки: {missing_columns}")
            
            # Конвертируем timestamp в datetime
            if df['timestamp'].dtype == 'object':
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            elif df['timestamp'].dtype in ['int64', 'float64']:
                # Предполагаем, что это Unix timestamp
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            
            # Сортируем по времени
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Проверяем корректность OHLC данных
            invalid_ohlc = df[(df['high'] < df['low']) | 
                             (df['high'] < df['open']) | 
                             (df['high'] < df['close']) |
                             (df['low'] > df['open']) | 
                             (df['low'] > df['close'])]
            
            if not invalid_ohlc.empty:
                print(f"Предупреждение: найдено {len(invalid_ohlc)} строк с некорректными OHLC данными")
            
            self.data = df
            self.symbol = symbol or file_path.stem
            
            print(f"Загружено {len(df)} записей для {self.symbol}")
            print(f"Период: {df['timestamp'].min()} - {df['timestamp'].max()}")
            
            return df
            
        except Exception as e:
            raise Exception(f"Ошибка при загрузке данных: {str(e)}")
    
    def load_from_api(self, 
                     symbol: str, 
                     timeframe: str, 
                     start_date: str = None, 
                     end_date: str = None,
                     exchange: str = 'binance',
                     limit: int = 1000) -> pd.DataFrame:
        """
        Загружает данные с биржи через CCXT
        
        Args:
            symbol: торговая пара (например, 'BTC/USDT')
            timeframe: таймфрейм ('1m', '5m', '15m', '1h', '4h', '1d')
            start_date: начальная дата в формате 'YYYY-MM-DD' или 'YYYY-MM-DD HH:MM:SS'
            end_date: конечная дата в формате 'YYYY-MM-DD' или 'YYYY-MM-DD HH:MM:SS'
            exchange: название биржи ('binance', 'okx', 'bybit', 'kucoin', etc.)
            limit: максимальное количество свечей за один запрос
            
        Returns:
            DataFrame с колонками: timestamp, open, high, low, close, volume
        """
        if not CCXT_AVAILABLE:
            raise ImportError("CCXT не установлен. Установите: pip install ccxt")
        
        try:
            # Создаем экземпляр биржи
            exchange_class = getattr(ccxt, exchange.lower())
            exchange_instance = exchange_class({
                'rateLimit': 1200,  # Ограничение запросов
                'enableRateLimit': True,
            })
            
            print(f"Подключение к бирже: {exchange_instance.name}")
            
            # Проверяем поддержку OHLCV
            if not exchange_instance.has['fetchOHLCV']:
                raise Exception(f"Биржа {exchange} не поддерживает загрузку OHLCV данных")
            
            # Проверяем доступность символа
            markets = exchange_instance.load_markets()
            if symbol not in markets:
                available_symbols = list(markets.keys())[:10]  # Показываем первые 10
                raise Exception(f"Символ {symbol} недоступен на {exchange}. "
                              f"Доступные символы (первые 10): {available_symbols}")
            
            # Проверяем поддержку таймфрейма
            if timeframe not in exchange_instance.timeframes:
                available_timeframes = list(exchange_instance.timeframes.keys())
                raise Exception(f"Таймфрейм {timeframe} не поддерживается на {exchange}. "
                              f"Доступные: {available_timeframes}")
            
            # Конвертируем даты в timestamp
            since = None
            until = None
            
            if start_date:
                since = self._parse_date_to_timestamp(start_date)
            
            if end_date:
                until = self._parse_date_to_timestamp(end_date)
            
            # Загружаем данные
            all_ohlcv = []
            current_since = since
            
            print(f"Загрузка данных {symbol} {timeframe} с {exchange}...")
            
            while True:
                try:
                    # Делаем запрос к бирже
                    ohlcv = exchange_instance.fetch_ohlcv(
                        symbol=symbol,
                        timeframe=timeframe,
                        since=current_since,
                        limit=limit
                    )
                    
                    if not ohlcv:
                        break
                    
                    # Фильтруем по конечной дате если указана
                    if until:
                        ohlcv = [candle for candle in ohlcv if candle[0] <= until]
                    
                    all_ohlcv.extend(ohlcv)
                    
                    # Проверяем, достигли ли конечной даты
                    if until and ohlcv and ohlcv[-1][0] >= until:
                        break
                    
                    # Обновляем timestamp для следующего запроса
                    if ohlcv:
                        current_since = ohlcv[-1][0] + 1
                    else:
                        break
                    
                    # Показываем прогресс
                    if len(all_ohlcv) % 5000 == 0:
                        last_date = datetime.fromtimestamp(ohlcv[-1][0] / 1000)
                        print(f"Загружено {len(all_ohlcv)} свечей, последняя дата: {last_date}")
                    
                    # Пауза между запросами для соблюдения лимитов
                    time.sleep(exchange_instance.rateLimit / 1000)
                    
                except ccxt.BaseError as e:
                    print(f"Ошибка при загрузке данных: {e}")
                    time.sleep(5)  # Пауза при ошибке
                    continue
            
            if not all_ohlcv:
                raise Exception("Не удалось загрузить данные")
            
            # Конвертируем в DataFrame
            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Конвертируем timestamp в datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Удаляем дубликаты и сортируем
            df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
            
            # Сохраняем информацию
            self.data = df
            self.symbol = symbol.replace('/', '')  # BTC/USDT -> BTCUSDT
            self.timeframe = timeframe
            
            print(f"Загружено {len(df)} записей для {symbol}")
            print(f"Период: {df['timestamp'].min()} - {df['timestamp'].max()}")
            
            return df
            
        except Exception as e:
            raise Exception(f"Ошибка при загрузке данных с {exchange}: {str(e)}")
    
    def _parse_date_to_timestamp(self, date_str: str) -> int:
        """Конвертирует строку даты в timestamp (миллисекунды)"""
        try:
            # Пробуем разные форматы
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d',
                '%d.%m.%Y %H:%M:%S',
                '%d.%m.%Y %H:%M',
                '%d.%m.%Y'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return int(dt.timestamp() * 1000)
                except ValueError:
                    continue
            
            raise ValueError(f"Неподдерживаемый формат даты: {date_str}")
            
        except Exception as e:
            raise ValueError(f"Ошибка парсинга даты '{date_str}': {str(e)}")
    
    def get_available_exchanges(self) -> List[str]:
        """Возвращает список доступных бирж"""
        if not CCXT_AVAILABLE:
            return []
        
        # Фильтруем только биржи с поддержкой OHLCV
        exchanges = []
        for exchange_id in ccxt.exchanges:
            try:
                exchange_class = getattr(ccxt, exchange_id)
                if hasattr(exchange_class, 'has') and exchange_class.has.get('fetchOHLCV', False):
                    exchanges.append(exchange_id)
            except:
                continue
        
        return sorted(exchanges)
    
    def get_exchange_info(self, exchange: str) -> dict:
        """Получает информацию о бирже"""
        if not CCXT_AVAILABLE:
            return {}
        
        try:
            exchange_class = getattr(ccxt, exchange.lower())
            exchange_instance = exchange_class()
            
            markets = exchange_instance.load_markets()
            
            return {
                'name': exchange_instance.name,
                'countries': getattr(exchange_instance, 'countries', []),
                'has_ohlcv': exchange_instance.has.get('fetchOHLCV', False),
                'timeframes': list(exchange_instance.timeframes.keys()) if hasattr(exchange_instance, 'timeframes') else [],
                'symbols_count': len(markets),
                'rate_limit': exchange_instance.rateLimit,
                'popular_symbols': [s for s in ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT'] if s in markets]
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def save_to_csv(self, filename: str = None, data: pd.DataFrame = None) -> str:
        """
        Сохраняет загруженные данные в CSV файл
        
        Args:
            filename: имя файла (если не указано, генерируется автоматически)
            data: данные для сохранения (если не указаны, используются загруженные)
            
        Returns:
            Путь к сохраненному файлу
        """
        df = data if data is not None else self.data
        
        if df is None:
            raise ValueError("Нет данных для сохранения")
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            symbol = self.symbol or "data"
            timeframe = self.timeframe or "unknown"
            filename = f"data/{symbol}_{timeframe}_{timestamp}.csv"
        
        # Создаем директорию если не существует
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем
        df.to_csv(filename, index=False)
        
        print(f"Данные сохранены в {filename}")
        return filename
    
    def filter_by_date(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Фильтрует данные по датам
        
        Args:
            start_date: начальная дата в формате 'YYYY-MM-DD'
            end_date: конечная дата в формате 'YYYY-MM-DD'
            
        Returns:
            Отфильтрованный DataFrame
        """
        if self.data is None:
            raise ValueError("Данные не загружены")
        
        df = self.data.copy()
        
        if start_date:
            start_date = pd.to_datetime(start_date)
            df = df[df['timestamp'] >= start_date]
        
        if end_date:
            end_date = pd.to_datetime(end_date)
            df = df[df['timestamp'] <= end_date]
        
        return df
    
    def get_price_at_timestamp(self, timestamp: pd.Timestamp, price_type: str = 'close') -> float:
        """
        Получает цену на определенный момент времени
        
        Args:
            timestamp: временная метка
            price_type: тип цены ('open', 'high', 'low', 'close')
            
        Returns:
            Цена
        """
        if self.data is None:
            raise ValueError("Данные не загружены")
        
        # Находим ближайшую временную метку
        idx = self.data['timestamp'].searchsorted(timestamp)
        
        if idx >= len(self.data):
            idx = len(self.data) - 1
        elif idx > 0 and abs(self.data.iloc[idx-1]['timestamp'] - timestamp) < abs(self.data.iloc[idx]['timestamp'] - timestamp):
            idx = idx - 1
        
        return self.data.iloc[idx][price_type]
    
    def validate_data(self) -> dict:
        """
        Проверяет качество загруженных данных
        
        Returns:
            Словарь с результатами проверки
        """
        if self.data is None:
            raise ValueError("Данные не загружены")
        
        df = self.data
        
        validation_results = {
            'total_records': len(df),
            'missing_values': df.isnull().sum().to_dict(),
            'duplicate_timestamps': df['timestamp'].duplicated().sum(),
            'data_gaps': [],
            'price_anomalies': 0
        }
        
        # Проверяем пропуски во времени
        time_diffs = df['timestamp'].diff().dropna()
        if len(time_diffs) > 1:
            median_diff = time_diffs.median()
            large_gaps = time_diffs[time_diffs > median_diff * 2]
            validation_results['data_gaps'] = len(large_gaps)
        
        # Проверяем аномалии в ценах (резкие скачки > 50%)
        price_changes = df['close'].pct_change().abs()
        validation_results['price_anomalies'] = (price_changes > 0.5).sum()
        
        return validation_results
    
    def get_summary(self) -> dict:
        """
        Возвращает сводную информацию о данных
        """
        if self.data is None:
            raise ValueError("Данные не загружены")
        
        df = self.data
        
        return {
            'symbol': self.symbol,
            'records_count': len(df),
            'date_range': {
                'start': df['timestamp'].min().strftime('%Y-%m-%d %H:%M:%S'),
                'end': df['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S')
            },
            'price_range': {
                'min': df['low'].min(),
                'max': df['high'].max(),
                'first_close': df['close'].iloc[0],
                'last_close': df['close'].iloc[-1]
            },
            'volume_stats': {
                'total': df['volume'].sum(),
                'average': df['volume'].mean(),
                'max': df['volume'].max()
            }
        } 