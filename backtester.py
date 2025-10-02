import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import json
from datetime import datetime
import time

from data_loader import DataLoader
from strategy import TradingStrategy

class Backtester:
    """
    Основной класс для проведения бэктестирования торговых стратегий
    """
    
    def __init__(self, config_path: str = None, config_dict: dict = None):
        """
        Инициализация бэктестера
        
        Args:
            config_path: путь к файлу конфигурации JSON
            config_dict: словарь с конфигурацией (альтернатива файлу)
        """
        if config_path:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        elif config_dict:
            self.config = config_dict
        else:
            raise ValueError("Необходимо указать либо config_path, либо config_dict")
        
        self.data_loader = DataLoader()
        self.strategy = TradingStrategy(self.config)
        self.results = {}
        self.execution_log = []
        
        # Параметры бэктеста
        self.start_date = self.config.get('start_date')
        self.end_date = self.config.get('end_date')
        self.data_source = self.config.get('data_source', {})
        self.symbol = self.config.get('symbol', 'UNKNOWN')
        
        # Для отслеживания прогресса
        self.total_ticks = 0
        self.processed_ticks = 0
        self.start_time = None
    
    def load_data(self, data_source: dict = None) -> pd.DataFrame:
        """
        Загружает исторические данные для бэктеста из различных источников
        
        Args:
            data_source: конфигурация источника данных (опционально)
            
        Returns:
            DataFrame с загруженными данными
        """
        source_config = data_source or self.data_source
        source_type = source_config.get('type', 'csv')
        
        data = None
        
        if source_type == 'csv':
            # Загрузка из CSV файла
            file_path = source_config.get('file')
            if not file_path:
                raise ValueError("Не указан файл с данными")
            
            print(f"Загрузка данных из CSV: {file_path}...")
            data = self.data_loader.load_from_csv(file_path, self.symbol)
            
        elif source_type == 'api':
            # Загрузка через API (CCXT)
            api_config = source_config.get('api', {})

            exchange = api_config.get('exchange', 'binance')
            api_symbol = api_config.get('symbol', 'BTC/USDT')
            timeframe = self.config.get('timeframe', '1h')
            auto_save = api_config.get('auto_save', False)
            market_type = api_config.get('market_type', 'spot')

            print(f"Загрузка данных через API с биржи {exchange}...")

            data = self.data_loader.load_from_api(
                symbol=api_symbol,
                timeframe=timeframe,
                start_date=self.start_date,
                end_date=self.end_date,
                exchange=exchange,
                market_type=market_type
            )
            
            # Автоматически сохраняем в CSV если включено
            if auto_save:
                saved_file = self.data_loader.save_to_csv()
                print(f"Данные автоматически сохранены в {saved_file}")
        
        else:
            raise ValueError(f"Неподдерживаемый тип источника данных: {source_type}")
        
        if data is None or data.empty:
            raise ValueError("Не удалось загрузить данные")
        
        # Фильтруем по дате если указано (для CSV данных)
        if source_type == 'csv' and (self.start_date or self.end_date):
            print(f"Фильтрация данных по периоду: {self.start_date} - {self.end_date}")
            data = self.data_loader.filter_by_date(self.start_date, self.end_date)
        
        # Проверяем качество данных
        validation = self.data_loader.validate_data()
        if validation['missing_values']:
            print(f"Предупреждение: найдены пропущенные значения: {validation['missing_values']}")
        
        if validation['price_anomalies'] > 0:
            print(f"Предупреждение: найдено {validation['price_anomalies']} аномалий в ценах")
        
        self.total_ticks = len(data)
        print(f"Подготовлено {self.total_ticks} тиков для бэктеста")
        
        return data
    
    def run_backtest(self, data: pd.DataFrame = None, verbose: bool = True) -> dict:
        """
        Запускает бэктест
        
        Args:
            data: данные для бэктеста (если не переданы, загружаются автоматически)
            verbose: выводить ли прогресс
            
        Returns:
            Результаты бэктеста
        """
        if data is None:
            data = self.load_data()
        
        print(f"\n{'='*50}")
        print(f"НАЧАЛО БЭКТЕСТА")
        print(f"{'='*50}")
        print(f"Символ: {self.symbol}")
        print(f"Период: {data['timestamp'].min()} - {data['timestamp'].max()}")
        print(f"Всего тиков: {len(data)}")
        print(f"Начальный баланс: ${self.strategy.initial_balance:,.2f}")
        print(f"Тип ордеров: {self.strategy.order_type.value.upper()}")
        print(f"DCA включен: {'Да' if self.strategy.dca_enabled else 'Нет'}")
        if self.strategy.dca_enabled:
            print(f"  - Макс. DCA ордеров: {self.strategy.max_dca_orders}")
            print(f"  - Шаг DCA: {self.strategy.step_price_value*100:.1f}%")
            print(f"  - Мультипликатор: {self.strategy.martingale_multiplier}x")
        print(f"Take Profit: {self.strategy.take_profit_percent*100:.1f}%")
        print(f"Stop Loss: {self.strategy.stop_loss_percent*100:.1f}%")
        print(f"{'='*50}\n")
        
        self.start_time = time.time()
        self.processed_ticks = 0
        
        # Передаем verbose флаг в стратегию
        self.strategy.verbose = verbose
        
        # Минимальный период для анализа
        lookback_period = max(self.strategy.lookback_period, 20)
        
        # Основной цикл бэктеста
        for i in range(lookback_period, len(data)):
            current_data = data.iloc[i]
            historical_data = data.iloc[:i+1]  # Все данные до текущего момента включительно
            
            # Обрабатываем текущий тик
            actions = self.strategy.process_tick(current_data, historical_data)
            
            # Логируем действия
            for action in actions:
                self.execution_log.append(action)
                
                if verbose and action['action'] in ['open_position', 'close_position', 'margin_call']:
                    if action['action'] == 'open_position':
                        print(f"[{current_data['timestamp']}] ВХОД: ${action['price']:.4f} | Кол-во: {action['quantity']:.6f}")
                        if self.strategy.leverage > 1:
                            position = self.strategy.get_open_position()
                            if position:
                                liquidation_price = self.strategy.calculate_liquidation_price(position)
                                print(f"   📊 Плечо: {self.strategy.leverage}x | Цена ликвидации: ${liquidation_price:.4f}")
                    elif action['action'] == 'close_position':
                        trade = action['trade_info']
                        pnl_sign = "+" if trade['pnl'] >= 0 else ""
                        avg_price = trade.get('average_price', trade['entry_price'])
                        
                        # Детальная информация о причине закрытия
                        reason_details = {
                            'take_profit': '✅ Take Profit достигнут',
                            'stop_loss': '🛑 Stop Loss сработал', 
                            'max_drawdown_reached': '🛑 Максимальная просадка превышена',
                            'trailing_take_profit': '✅ Trailing Take Profit сработал',
                            'trailing_stop_loss': '🛑 Trailing Stop Loss сработал',
                            'margin_call': '⚠️ Маржин колл'
                        }
                        
                        reason_text = reason_details.get(trade['reason'], f"❓ {trade['reason']}")
                        
                        if trade['reason'] == 'max_drawdown_reached':
                            print(f"🛑 [{current_data['timestamp']}] ЗАКРЫТИЕ ПО ПРОСАДКЕ")
                            print(f"   💰 Цена выхода: ${action['trade_info']['exit_price']:.4f}")
                            print(f"   📊 Средняя цена входа: ${avg_price:.4f}")
                            print(f"   💸 PnL: {pnl_sign}${trade['pnl']:.2f} ({pnl_sign}{trade['pnl_percent']:.2f}%)")
                            print(f"   📉 Причина: {reason_text}")
                            print(f"   🔢 DCA ордеров: {trade.get('dca_orders', 'N/A')}")
                        else:
                            print(f"[{current_data['timestamp']}] ВЫХОД: ${action['trade_info']['exit_price']:.4f}")
                            print(f"   📊 Средняя цена: ${avg_price:.4f}")
                            print(f"   💸 PnL: {pnl_sign}${trade['pnl']:.2f} ({pnl_sign}{trade['pnl_percent']:.2f}%)")
                            print(f"   📋 Причина: {reason_text}")
                            print(f"   🔢 DCA ордеров: {trade.get('dca_orders', 'N/A')}")
                    elif action['action'] == 'margin_call':
                        trade = action['trade_info']
                        pnl_sign = "+" if trade['pnl'] >= 0 else ""
                        avg_price = trade.get('average_price', trade['entry_price'])
                        print(f"⚠️  [{current_data['timestamp']}] ЛИКВИДАЦИЯ: ${action['trade_info']['exit_price']:.4f} | "
                              f"Средняя цена: ${avg_price:.4f} | "
                              f"PnL: {pnl_sign}${trade['pnl']:.2f} ({pnl_sign}{trade['pnl_percent']:.2f}%) | "
                              f"Причина: {action['reason']}")
                        print(f"   💥 Позиция ликвидирована из-за недостатка маржи!")
            
            self.processed_ticks += 1
            
            # Показываем прогресс каждые 1000 тиков
            if verbose and self.processed_ticks % 1000 == 0:
                progress = (self.processed_ticks / (self.total_ticks - lookback_period)) * 100
                elapsed = time.time() - self.start_time
                print(f"Прогресс: {progress:.1f}% | Время: {elapsed:.1f}с | Баланс: ${self.strategy.balance:.2f}")
        
        # Закрываем открытые позиции по последней цене
        if self.strategy.has_open_position():
            last_price = data.iloc[-1]['close']
            last_timestamp = data.iloc[-1]['timestamp']
            trade_info = self.strategy.close_position(last_price, last_timestamp, "end_of_data")
            
            if verbose:
                avg_price = trade_info.get('average_price', trade_info['entry_price'])
                print(f"[{last_timestamp}] Принудительное закрытие позиции по цене ${last_price:.4f}")
                print(f"Средняя цена: ${avg_price:.4f}")
                pnl_sign = "+" if trade_info['pnl'] >= 0 else ""
                print(f"PnL: {pnl_sign}${trade_info['pnl']:.2f} ({pnl_sign}{trade_info['pnl_percent']:.2f}%)")
        
        # Собираем результаты
        self.results = self._compile_results(data)
        
        if verbose:
            self._print_results()
        
        return self.results
    
    def _compile_results(self, data: pd.DataFrame) -> dict:
        """Компилирует результаты бэктеста"""
        stats = self.strategy.get_statistics()
        
        # Исключаем сделки с "end_of_data" из всех расчетов
        completed_trades = [t for t in self.strategy.trade_history if t['reason'] != 'end_of_data']
        
        # Дополнительные метрики
        if completed_trades:
            # Максимальная просадка
            balance_history = self._calculate_balance_history(data)
            max_drawdown = self._calculate_max_drawdown(balance_history)
            
            # Sharpe ratio (упрощенный)
            returns = pd.Series([t['pnl_percent']/100 for t in completed_trades])
            sharpe_ratio = returns.mean() / returns.std() if returns.std() > 0 else 0
            
            # Profit factor
            gross_profit = sum(t['pnl'] for t in completed_trades if t['pnl'] > 0)
            gross_loss = abs(sum(t['pnl'] for t in completed_trades if t['pnl'] < 0))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            # Средняя длительность сделки
            durations = []
            for trade in completed_trades:
                duration = (trade['exit_time'] - trade['entry_time']).total_seconds() / 3600  # в часах
                durations.append(duration)
            avg_trade_duration = np.mean(durations) if durations else 0
            
        else:
            max_drawdown = 0
            sharpe_ratio = 0
            profit_factor = 0
            avg_trade_duration = 0
            balance_history = []
        
        results = {
            'config': self.config,
            'basic_stats': stats,
            'advanced_metrics': {
                'max_drawdown_percent': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'profit_factor': profit_factor,
                'avg_trade_duration_hours': avg_trade_duration,
                'total_fees': 0,  # Пока не учитываем комиссии
                'max_consecutive_wins': self._get_max_consecutive(True),
                'max_consecutive_losses': self._get_max_consecutive(False)
            },
            'trade_history': self.strategy.trade_history,
            'execution_log': self.execution_log,
            'balance_history': balance_history,
            'data_summary': self.data_loader.get_summary() if self.data_loader.data is not None else {},
            'backtest_info': {
                'start_time': self.start_time,
                'end_time': time.time(),
                'duration_seconds': time.time() - self.start_time if self.start_time else 0,
                'processed_ticks': self.processed_ticks,
                'total_ticks': self.total_ticks
            }
        }
        
        return results
    
    def _calculate_balance_history(self, data: pd.DataFrame) -> List[dict]:
        """Вычисляет историю изменения баланса"""
        balance_history = []
        current_balance = self.strategy.initial_balance
        
        # Используем только завершенные сделки
        completed_trades = [t for t in self.strategy.trade_history if t['reason'] != 'end_of_data']
        
        for trade in completed_trades:
            balance_history.append({
                'timestamp': trade['exit_time'],
                'balance': current_balance + trade['pnl'],
                'pnl': trade['pnl'],
                'cumulative_pnl': sum(t['pnl'] for t in completed_trades 
                                    if t['exit_time'] <= trade['exit_time'])
            })
            current_balance += trade['pnl']
        
        return balance_history
    
    def _calculate_max_drawdown(self, balance_history: List[dict]) -> float:
        """Вычисляет максимальную просадку в процентах"""
        if not balance_history:
            return 0
        
        balances = [self.strategy.initial_balance] + [b['balance'] for b in balance_history]
        
        max_balance = self.strategy.initial_balance
        max_drawdown = 0
        
        for balance in balances:
            if balance > max_balance:
                max_balance = balance
            
            drawdown = (max_balance - balance) / max_balance * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown
    
    def _get_max_consecutive(self, wins: bool) -> int:
        """Получает максимальное количество последовательных побед/поражений"""
        # Используем только завершенные сделки
        completed_trades = [t for t in self.strategy.trade_history if t['reason'] != 'end_of_data']
        
        if not completed_trades:
            return 0
        
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in completed_trades:
            is_win = trade['pnl'] > 0
            
            if (wins and is_win) or (not wins and not is_win):
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _print_results(self):
        """Выводит результаты бэктеста"""
        stats = self.results['basic_stats']
        advanced = self.results['advanced_metrics']
        
        print(f"\n{'='*50}")
        print(f"РЕЗУЛЬТАТЫ БЭКТЕСТА")
        print(f"{'='*50}")
        
        print(f"\n📊 ОСНОВНЫЕ ПОКАЗАТЕЛИ:")
        print(f"Начальный баланс: ${self.strategy.initial_balance:,.2f}")
        print(f"Финальный баланс (завершенные сделки): ${stats['current_balance']:,.2f}")
        if 'actual_balance' in stats and stats['actual_balance'] != stats['current_balance']:
            print(f"Реальный баланс (с незавершенными): ${stats['actual_balance']:,.2f}")
        print(f"Общая прибыль: ${stats['total_pnl']:,.2f}")
        print(f"Общая доходность: {stats['total_return']:.2f}%")
        print(f"Максимальная просадка: {advanced['max_drawdown_percent']:.2f}%")
        
        print(f"\n📈 СТАТИСТИКА СДЕЛОК:")
        print(f"Всего сделок: {stats['total_trades']}")
        print(f"Прибыльных: {stats['winning_trades']} ({stats['win_rate']:.1f}%)")
        print(f"Убыточных: {stats['losing_trades']} ({100-stats['win_rate']:.1f}%)")
        print(f"Средняя прибыль: ${stats['average_pnl']:.2f}")
        print(f"Максимальная прибыль: ${stats['max_profit']:.2f}")
        print(f"Максимальный убыток: ${stats['max_loss']:.2f}")
        
        if stats['total_trades'] > 0:
            print(f"Средняя прибыльная сделка: ${stats['average_profit']:.2f}")
            print(f"Средняя убыточная сделка: ${stats['average_loss']:.2f}")
        
        # Показываем информацию о незавершенных позициях
        if 'open_positions' in stats and stats['open_positions'] > 0:
            print(f"\n⚠️  НЕЗАВЕРШЕННЫЕ ПОЗИЦИИ:")
            print(f"Позиций не закрыто: {stats['open_positions']}")
            print(f"* Эти позиции исключены из статистики, так как не были закрыты по стратегии")
            
            # Показываем детали незавершенных сделок
            open_trades = [t for t in self.strategy.trade_history if t['reason'] == 'end_of_data']
            if open_trades:
                print(f"\n📋 ДЕТАЛИ НЕЗАВЕРШЕННЫХ СДЕЛОК:")
                for i, trade in enumerate(open_trades, 1):
                    avg_price = trade.get('average_price', trade['entry_price'])
                    print(f"{i}. {trade['symbol']} | Вход: ${trade['entry_price']:.4f} | "
                          f"Средняя цена: ${avg_price:.4f} | "
                          f"Количество: {trade['quantity']:.6f} | "
                          f"DCA ордеров: {trade['dca_orders_count']}")
        
        print(f"\n🔢 ДОПОЛНИТЕЛЬНЫЕ МЕТРИКИ:")
        print(f"Profit Factor: {advanced['profit_factor']:.2f}")
        print(f"Sharpe Ratio: {advanced['sharpe_ratio']:.2f}")
        print(f"Средняя длительность сделки: {advanced['avg_trade_duration_hours']:.1f} часов")
        print(f"Макс. подряд побед: {advanced['max_consecutive_wins']}")
        print(f"Макс. подряд поражений: {advanced['max_consecutive_losses']}")
        
        print(f"\n⏱️  ИНФОРМАЦИЯ О ТЕСТЕ:")
        duration = self.results['backtest_info']['duration_seconds']
        print(f"Время выполнения: {duration:.2f} секунд")
        print(f"Обработано тиков: {self.processed_ticks:,}")
        print(f"Скорость: {self.processed_ticks/duration:.0f} тиков/сек")
        
        
        print(f"\n{'='*50}")
    
    def save_results(self, filename: str = None):
        """
        Сохраняет результаты в JSON файл
        
        Args:
            filename: имя файла для сохранения
            
        Returns:
            Имя сохраненного файла
        """
        # Создаем директорию results если её нет
        import os
        os.makedirs('results', exist_ok=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_results_{timestamp}.json"
        
        # Сохраняем в директорию results
        filepath = os.path.join('results', filename)
        
        # Конвертируем datetime объекты в строки для JSON
        results_copy = self._prepare_for_json(self.results.copy())
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_copy, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _prepare_for_json(self, obj):
        """Подготавливает объект для сериализации в JSON"""
        if isinstance(obj, dict):
            return {key: self._prepare_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._prepare_for_json(item) for item in obj]
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    def get_trade_summary(self) -> pd.DataFrame:
        """Возвращает сводку по сделкам в виде DataFrame"""
        if not self.strategy.trade_history:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.strategy.trade_history)
        
        # Добавляем дополнительные колонки
        df['duration_hours'] = (df['exit_time'] - df['entry_time']).dt.total_seconds() / 3600
        df['profit_loss'] = df['pnl'].apply(lambda x: 'Profit' if x > 0 else 'Loss')
        
        return df 