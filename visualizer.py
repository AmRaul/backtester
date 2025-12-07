import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import os


class BacktestVisualizer:
    """
    Класс для визуализации результатов бэктестинга
    Создает интерактивные графики с помощью plotly
    """

    def __init__(self, results: dict, data: pd.DataFrame = None):
        """
        Инициализация визуализатора

        Args:
            results: результаты бэктеста из Backtester.results
            data: OHLCV данные (опционально, если есть в results)
        """
        self.results = results
        self.trade_history = results.get('trade_history', [])
        self.balance_history = results.get('balance_history', [])
        self.execution_log = results.get('execution_log', [])
        self.config = results.get('config', {})
        self.stats = results.get('basic_stats', {})
        self.advanced_metrics = results.get('advanced_metrics', {})

        # OHLCV данные
        self.data = data

        # Фильтруем end_of_data сделки
        self.completed_trades = [t for t in self.trade_history if t['reason'] != 'end_of_data']

    def plot_price_and_trades(self,
                              show_dca: bool = True,
                              show_levels: bool = True,
                              height: int = 800) -> go.Figure:
        """
        Создает свечной график с метками всех сделок

        Args:
            show_dca: показывать ли DCA ордера
            show_levels: показывать ли уровни TP/SL
            height: высота графика в пикселях

        Returns:
            plotly Figure
        """
        if self.data is None or self.data.empty:
            raise ValueError("Нет данных для отображения графика цены")

        # Создаем фигуру
        fig = go.Figure()

        # Добавляем свечной график
        fig.add_trace(go.Candlestick(
            x=self.data['timestamp'],
            open=self.data['open'],
            high=self.data['high'],
            low=self.data['low'],
            close=self.data['close'],
            name='Цена',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ))

        # Добавляем метки сделок
        if self.completed_trades:
            self._add_trade_markers(fig, show_dca, show_levels)

        # Настройка внешнего вида
        fig.update_layout(
            title=f"График цены и сделок - {self.config.get('symbol', 'Unknown')}",
            xaxis_title="Время",
            yaxis_title="Цена",
            height=height,
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            template='plotly_dark',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        return fig

    def _add_trade_markers(self, fig: go.Figure, show_dca: bool, show_levels: bool):
        """Добавляет метки входов/выходов на график"""

        # Списки для группировки меток
        entry_times = []
        entry_prices = []
        entry_text = []

        exit_times_profit = []
        exit_prices_profit = []
        exit_text_profit = []

        exit_times_loss = []
        exit_prices_loss = []
        exit_text_loss = []

        dca_times = []
        dca_prices = []
        dca_text = []

        for trade in self.completed_trades:
            # Вход (первый ордер)
            entry_times.append(trade['entry_time'])
            entry_prices.append(trade['entry_price'])
            entry_info = (
                f"Вход<br>"
                f"Цена: ${trade['entry_price']:.4f}<br>"
                f"Количество: {trade['quantity']:.6f}<br>"
                f"Время: {trade['entry_time']}"
            )
            entry_text.append(entry_info)

            # Выход
            exit_time = trade['exit_time']
            exit_price = trade['exit_price']
            avg_price = trade.get('average_price', trade['entry_price'])
            pnl = trade['pnl']
            pnl_percent = trade['pnl_percent']

            reason_map = {
                'take_profit': 'Take Profit',
                'stop_loss': 'Stop Loss',
                'trailing_take_profit': 'Trailing TP',
                'trailing_stop_loss': 'Trailing SL',
                'max_drawdown_reached': 'Max Drawdown',
                'margin_call': 'Margin Call',
                'liquidation_price_reached': 'Liquidation'
            }

            reason_text = reason_map.get(trade['reason'], trade['reason'])

            exit_info = (
                f"Выход<br>"
                f"Цена: ${exit_price:.4f}<br>"
                f"Средняя цена входа: ${avg_price:.4f}<br>"
                f"PnL: ${pnl:.2f} ({pnl_percent:+.2f}%)<br>"
                f"Причина: {reason_text}<br>"
                f"Время: {exit_time}"
            )

            if pnl >= 0:
                exit_times_profit.append(exit_time)
                exit_prices_profit.append(exit_price)
                exit_text_profit.append(exit_info)
            else:
                exit_times_loss.append(exit_time)
                exit_prices_loss.append(exit_price)
                exit_text_loss.append(exit_info)

            # DCA ордера
            if show_dca and trade.get('dca_orders_count', 0) > 0:
                # Находим DCA ордера в execution_log
                dca_orders = [
                    log for log in self.execution_log
                    if log.get('action') == 'dca_order' and
                    log['timestamp'] >= trade['entry_time'] and
                    log['timestamp'] <= trade['exit_time']
                ]

                for dca in dca_orders:
                    dca_times.append(dca['timestamp'])
                    dca_prices.append(dca['price'])
                    dca_level = dca.get('dca_level', '?')
                    dca_info = (
                        f"DCA #{dca_level}<br>"
                        f"Цена: ${dca['price']:.4f}<br>"
                        f"Количество: {dca['quantity']:.6f}<br>"
                        f"Время: {dca['timestamp']}"
                    )
                    dca_text.append(dca_info)

            # Уровни TP/SL
            if show_levels:
                self._add_trade_levels(fig, trade)

        # Добавляем метки входов
        if entry_times:
            fig.add_trace(go.Scatter(
                x=entry_times,
                y=entry_prices,
                mode='markers',
                name='Вход',
                marker=dict(
                    symbol='triangle-up',
                    size=15,
                    color='#00ff00',
                    line=dict(width=2, color='white')
                ),
                text=entry_text,
                hovertemplate='%{text}<extra></extra>'
            ))

        # Добавляем метки выходов в прибыль
        if exit_times_profit:
            fig.add_trace(go.Scatter(
                x=exit_times_profit,
                y=exit_prices_profit,
                mode='markers',
                name='Выход (прибыль)',
                marker=dict(
                    symbol='triangle-down',
                    size=15,
                    color='#26a69a',
                    line=dict(width=2, color='white')
                ),
                text=exit_text_profit,
                hovertemplate='%{text}<extra></extra>'
            ))

        # Добавляем метки выходов в убыток
        if exit_times_loss:
            fig.add_trace(go.Scatter(
                x=exit_times_loss,
                y=exit_prices_loss,
                mode='markers',
                name='Выход (убыток)',
                marker=dict(
                    symbol='triangle-down',
                    size=15,
                    color='#ef5350',
                    line=dict(width=2, color='white')
                ),
                text=exit_text_loss,
                hovertemplate='%{text}<extra></extra>'
            ))

        # Добавляем метки DCA
        if dca_times:
            fig.add_trace(go.Scatter(
                x=dca_times,
                y=dca_prices,
                mode='markers',
                name='DCA ордера',
                marker=dict(
                    symbol='triangle-up',
                    size=10,
                    color='#ffa726',
                    line=dict(width=1, color='white')
                ),
                text=dca_text,
                hovertemplate='%{text}<extra></extra>'
            ))

    def _add_trade_levels(self, fig: go.Figure, trade: dict):
        """Добавляет линии уровней для сделки"""
        entry_time = trade['entry_time']
        exit_time = trade['exit_time']
        avg_price = trade.get('average_price', trade['entry_price'])

        # Средняя цена входа
        fig.add_trace(go.Scatter(
            x=[entry_time, exit_time],
            y=[avg_price, avg_price],
            mode='lines',
            line=dict(color='#2196f3', width=1, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ))

        # Take Profit уровень
        if self.config.get('take_profit', {}).get('enabled', True):
            tp_percent = self.config.get('take_profit', {}).get('percent', 5) / 100
            order_type = self.config.get('order_type', 'long')

            if order_type == 'long':
                tp_price = avg_price * (1 + tp_percent)
            else:
                tp_price = avg_price * (1 - tp_percent)

            fig.add_trace(go.Scatter(
                x=[entry_time, exit_time],
                y=[tp_price, tp_price],
                mode='lines',
                line=dict(color='#4caf50', width=1, dash='dash'),
                showlegend=False,
                hoverinfo='skip'
            ))

        # Stop Loss уровень
        if self.config.get('stop_loss', {}).get('enabled', True):
            sl_percent = self.config.get('stop_loss', {}).get('percent', 10) / 100
            order_type = self.config.get('order_type', 'long')

            if order_type == 'long':
                sl_price = avg_price * (1 - sl_percent)
            else:
                sl_price = avg_price * (1 + sl_percent)

            fig.add_trace(go.Scatter(
                x=[entry_time, exit_time],
                y=[sl_price, sl_price],
                mode='lines',
                line=dict(color='#f44336', width=1, dash='dash'),
                showlegend=False,
                hoverinfo='skip'
            ))

    def plot_balance(self, height: int = 400) -> go.Figure:
        """
        График изменения баланса

        Args:
            height: высота графика

        Returns:
            plotly Figure
        """
        if not self.balance_history:
            # Создаем упрощенный график на основе сделок
            if not self.completed_trades:
                raise ValueError("Нет данных о балансе или сделках")

            timestamps = [self.stats.get('initial_balance', 1000)]
            balances = [self.stats.get('initial_balance', 1000)]

            current_balance = self.stats.get('initial_balance', 1000)
            for trade in self.completed_trades:
                current_balance += trade['pnl']
                timestamps.append(trade['exit_time'])
                balances.append(current_balance)
        else:
            timestamps = [b['timestamp'] for b in self.balance_history]
            balances = [b['balance'] for b in self.balance_history]

        # Создаем график
        fig = go.Figure()

        initial_balance = self.config.get('start_balance', 1000)

        # Линия баланса
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=balances,
            mode='lines',
            name='Баланс',
            line=dict(color='#2196f3', width=2),
            fill='tonexty'
        ))

        # Линия начального баланса
        if timestamps:
            fig.add_trace(go.Scatter(
                x=[timestamps[0], timestamps[-1]],
                y=[initial_balance, initial_balance],
                mode='lines',
                name='Начальный баланс',
                line=dict(color='gray', width=1, dash='dash')
            ))

        fig.update_layout(
            title="Динамика баланса",
            xaxis_title="Время",
            yaxis_title="Баланс ($)",
            height=height,
            template='plotly_dark',
            hovermode='x unified'
        )

        return fig

    def plot_pnl(self, height: int = 400) -> go.Figure:
        """
        График кумулятивного PnL

        Args:
            height: высота графика

        Returns:
            plotly Figure
        """
        if not self.completed_trades:
            raise ValueError("Нет завершенных сделок для отображения PnL")

        # Подготовка данных
        timestamps = [trade['exit_time'] for trade in self.completed_trades]
        pnls = [trade['pnl'] for trade in self.completed_trades]
        cumulative_pnl = np.cumsum(pnls)

        # Создаем график с двумя осями Y
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Столбчатый график отдельных сделок
        colors = ['#26a69a' if pnl >= 0 else '#ef5350' for pnl in pnls]

        fig.add_trace(
            go.Bar(
                x=timestamps,
                y=pnls,
                name='PnL сделки',
                marker_color=colors,
                opacity=0.6
            ),
            secondary_y=False
        )

        # Линия кумулятивного PnL
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=cumulative_pnl,
                name='Кумулятивный PnL',
                line=dict(color='#ffa726', width=3),
                mode='lines+markers'
            ),
            secondary_y=True
        )

        # Настройка осей
        fig.update_xaxes(title_text="Время")
        fig.update_yaxes(title_text="PnL сделки ($)", secondary_y=False)
        fig.update_yaxes(title_text="Кумулятивный PnL ($)", secondary_y=True)

        fig.update_layout(
            title="Прибыль/Убыток по сделкам",
            height=height,
            template='plotly_dark',
            hovermode='x unified'
        )

        return fig

    def plot_drawdown(self, height: int = 400) -> go.Figure:
        """
        График просадки

        Args:
            height: высота графика

        Returns:
            plotly Figure
        """
        if not self.balance_history:
            raise ValueError("Нет данных о балансе для расчета просадки")

        # Рассчитываем просадку
        timestamps = [b['timestamp'] for b in self.balance_history]
        balances = [b['balance'] for b in self.balance_history]

        peak = self.config.get('start_balance', 1000)
        drawdowns = []

        for balance in balances:
            if balance > peak:
                peak = balance
            drawdown = ((peak - balance) / peak) * 100
            drawdowns.append(drawdown)

        # Создаем график
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=timestamps,
            y=drawdowns,
            mode='lines',
            name='Просадка',
            line=dict(color='#ef5350', width=2),
            fill='tozeroy',
            fillcolor='rgba(239, 83, 80, 0.3)'
        ))

        # Линия максимальной просадки
        max_dd = self.advanced_metrics.get('max_drawdown_percent', 0)
        if timestamps:
            fig.add_trace(go.Scatter(
                x=[timestamps[0], timestamps[-1]],
                y=[max_dd, max_dd],
                mode='lines',
                name=f'Max DD: {max_dd:.2f}%',
                line=dict(color='red', width=2, dash='dash')
            ))

        fig.update_layout(
            title="Просадка от пика",
            xaxis_title="Время",
            yaxis_title="Просадка (%)",
            height=height,
            template='plotly_dark',
            hovermode='x unified'
        )

        return fig

    def plot_trade_distribution(self, height: int = 400) -> go.Figure:
        """
        Распределение прибыльных и убыточных сделок

        Args:
            height: высота графика

        Returns:
            plotly Figure
        """
        if not self.completed_trades:
            raise ValueError("Нет завершенных сделок")

        # Разделяем на прибыльные и убыточные
        profits = [t['pnl'] for t in self.completed_trades if t['pnl'] > 0]
        losses = [t['pnl'] for t in self.completed_trades if t['pnl'] <= 0]

        fig = go.Figure()

        # Гистограмма прибыльных сделок
        if profits:
            fig.add_trace(go.Histogram(
                x=profits,
                name='Прибыльные',
                marker_color='#26a69a',
                opacity=0.7,
                nbinsx=20
            ))

        # Гистограмма убыточных сделок
        if losses:
            fig.add_trace(go.Histogram(
                x=losses,
                name='Убыточные',
                marker_color='#ef5350',
                opacity=0.7,
                nbinsx=20
            ))

        fig.update_layout(
            title="Распределение PnL",
            xaxis_title="PnL ($)",
            yaxis_title="Количество сделок",
            height=height,
            template='plotly_dark',
            barmode='overlay'
        )

        return fig

    def plot_all(self, height: int = 1600) -> go.Figure:
        """
        Все графики в одном окне

        Args:
            height: общая высота графика

        Returns:
            plotly Figure
        """
        # Создаем subplot с 4 графиками
        fig = make_subplots(
            rows=4, cols=1,
            subplot_titles=(
                'График цены и сделок',
                'Динамика баланса',
                'Кумулятивный PnL',
                'Просадка'
            ),
            row_heights=[0.4, 0.2, 0.2, 0.2],
            vertical_spacing=0.08
        )

        # График 1: Цена и сделки
        if self.data is not None and not self.data.empty:
            fig.add_trace(
                go.Candlestick(
                    x=self.data['timestamp'],
                    open=self.data['open'],
                    high=self.data['high'],
                    low=self.data['low'],
                    close=self.data['close'],
                    name='Цена',
                    increasing_line_color='#26a69a',
                    decreasing_line_color='#ef5350'
                ),
                row=1, col=1
            )

            # Добавляем метки сделок (упрощенно)
            if self.completed_trades:
                entry_times = [t['entry_time'] for t in self.completed_trades]
                entry_prices = [t['entry_price'] for t in self.completed_trades]
                exit_times = [t['exit_time'] for t in self.completed_trades]
                exit_prices = [t['exit_price'] for t in self.completed_trades]

                fig.add_trace(
                    go.Scatter(
                        x=entry_times, y=entry_prices,
                        mode='markers',
                        marker=dict(symbol='triangle-up', size=10, color='green'),
                        name='Вход',
                        showlegend=False
                    ),
                    row=1, col=1
                )

                fig.add_trace(
                    go.Scatter(
                        x=exit_times, y=exit_prices,
                        mode='markers',
                        marker=dict(symbol='triangle-down', size=10,
                                   color=['#26a69a' if t['pnl'] >= 0 else '#ef5350'
                                          for t in self.completed_trades]),
                        name='Выход',
                        showlegend=False
                    ),
                    row=1, col=1
                )

        # График 2: Баланс
        if self.balance_history:
            timestamps = [b['timestamp'] for b in self.balance_history]
            balances = [b['balance'] for b in self.balance_history]

            fig.add_trace(
                go.Scatter(
                    x=timestamps, y=balances,
                    mode='lines',
                    line=dict(color='#2196f3', width=2),
                    name='Баланс',
                    showlegend=False
                ),
                row=2, col=1
            )

        # График 3: PnL
        if self.completed_trades:
            timestamps = [t['exit_time'] for t in self.completed_trades]
            cumulative_pnl = np.cumsum([t['pnl'] for t in self.completed_trades])

            fig.add_trace(
                go.Scatter(
                    x=timestamps, y=cumulative_pnl,
                    mode='lines',
                    line=dict(color='#ffa726', width=2),
                    name='Cumulative PnL',
                    showlegend=False
                ),
                row=3, col=1
            )

        # График 4: Просадка
        if self.balance_history:
            timestamps = [b['timestamp'] for b in self.balance_history]
            balances = [b['balance'] for b in self.balance_history]

            peak = self.config.get('start_balance', 1000)
            drawdowns = []
            for balance in balances:
                if balance > peak:
                    peak = balance
                drawdown = ((peak - balance) / peak) * 100
                drawdowns.append(drawdown)

            fig.add_trace(
                go.Scatter(
                    x=timestamps, y=drawdowns,
                    mode='lines',
                    line=dict(color='#ef5350', width=2),
                    fill='tozeroy',
                    name='Drawdown',
                    showlegend=False
                ),
                row=4, col=1
            )

        # Обновляем layout
        fig.update_layout(
            height=height,
            template='plotly_dark',
            showlegend=False,
            title_text=f"Отчет по бэктесту - {self.config.get('symbol', 'Unknown')}"
        )

        fig.update_xaxes(rangeslider_visible=False, row=1, col=1)

        return fig

    def save_html(self, filename: str = None, fig: go.Figure = None) -> str:
        """
        Сохраняет график в HTML файл

        Args:
            filename: имя файла (если не указано, генерируется автоматически)
            fig: график для сохранения (если None, создается plot_all)

        Returns:
            Путь к сохраненному файлу
        """
        # Создаем директорию results если её нет
        os.makedirs('results', exist_ok=True)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            symbol = self.config.get('symbol', 'backtest')
            filename = f"results/{symbol}_visualization_{timestamp}.html"

        # Создаем график если не передан
        if fig is None:
            fig = self.plot_all()

        # Сохраняем
        fig.write_html(filename)

        return filename

    def get_summary_stats(self) -> dict:
        """
        Возвращает сводную статистику для отображения

        Returns:
            Словарь со статистикой
        """
        return {
            'Символ': self.config.get('symbol', 'Unknown'),
            'Таймфрейм': self.config.get('timeframe', 'Unknown'),
            'Начальный баланс': f"${self.config.get('start_balance', 0):,.2f}",
            'Финальный баланс': f"${self.stats.get('current_balance', 0):,.2f}",
            'Общая прибыль': f"${self.stats.get('total_pnl', 0):,.2f}",
            'Доходность': f"{self.stats.get('total_return', 0):.2f}%",
            'Всего сделок': self.stats.get('total_trades', 0),
            'Прибыльных': f"{self.stats.get('winning_trades', 0)} ({self.stats.get('win_rate', 0):.1f}%)",
            'Убыточных': f"{self.stats.get('losing_trades', 0)}",
            'Макс. просадка': f"{self.advanced_metrics.get('max_drawdown_percent', 0):.2f}%",
            'Profit Factor': f"{self.advanced_metrics.get('profit_factor', 0):.2f}",
            'Sharpe Ratio': f"{self.advanced_metrics.get('sharpe_ratio', 0):.2f}"
        }
