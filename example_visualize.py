"""
Пример использования визуализации результатов бэктестинга

Демонстрирует:
1. Запуск бэктеста
2. Различные типы графиков
3. Сохранение интерактивных отчетов в HTML
"""

from backtester import Backtester


def example_basic_visualization():
    """Базовый пример визуализации"""
    print("\n" + "="*70)
    print("ПРИМЕР 1: Базовая визуализация всех графиков")
    print("="*70 + "\n")

    # Создаем бэктестер
    bt = Backtester(config_path='config.json')

    # Запускаем бэктест
    results = bt.run_backtest(verbose=False)

    # Визуализируем все графики
    fig = bt.visualize_results(
        graph_type='all',          # Все графики в одном окне
        save_html=True,            # Сохранить в HTML
        filename='results/backtest_report_all.html'
    )

    # Показываем график в браузере
    fig.show()


def example_individual_charts():
    """Пример создания отдельных графиков"""
    print("\n" + "="*70)
    print("ПРИМЕР 2: Отдельные графики")
    print("="*70 + "\n")

    # Создаем и запускаем бэктест
    bt = Backtester(config_path='config.json')
    results = bt.run_backtest(verbose=False)

    # График 1: Цена и сделки
    print("📊 Создание графика цены и сделок...")
    fig_price = bt.visualize_results(
        graph_type='price',
        show_dca=True,             # Показать DCA ордера
        show_levels=True,          # Показать уровни TP/SL
        save_html=True,
        filename='results/price_and_trades.html'
    )

    # График 2: Динамика баланса
    print("📈 Создание графика баланса...")
    fig_balance = bt.visualize_results(
        graph_type='balance',
        save_html=True,
        filename='results/balance.html'
    )

    # График 3: Кумулятивный PnL
    print("💰 Создание графика PnL...")
    fig_pnl = bt.visualize_results(
        graph_type='pnl',
        save_html=True,
        filename='results/pnl.html'
    )

    # График 4: Просадка
    print("📉 Создание графика просадки...")
    fig_drawdown = bt.visualize_results(
        graph_type='drawdown',
        save_html=True,
        filename='results/drawdown.html'
    )

    # График 5: Распределение сделок
    print("📊 Создание графика распределения...")
    fig_distribution = bt.visualize_results(
        graph_type='distribution',
        save_html=True,
        filename='results/distribution.html'
    )

    print("\n✅ Все графики сохранены в папке 'results/'")

    # Показываем основной график
    fig_price.show()


def example_with_direct_visualizer():
    """Пример прямого использования BacktestVisualizer"""
    print("\n" + "="*70)
    print("ПРИМЕР 3: Прямое использование BacktestVisualizer")
    print("="*70 + "\n")

    from visualizer import BacktestVisualizer

    # Запускаем бэктест
    bt = Backtester(config_path='config.json')
    results = bt.run_backtest(verbose=False)

    # Получаем данные
    data = bt.execution_data if bt.use_dual_timeframe else bt.data_loader.data

    # Создаем визуализатор напрямую
    viz = BacktestVisualizer(results, data)

    # Получаем статистику
    print("\n📊 Сводная статистика:")
    stats = viz.get_summary_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Создаем кастомный график
    fig = viz.plot_price_and_trades(
        show_dca=True,
        show_levels=True,
        height=1000  # Увеличенная высота
    )

    # Сохраняем
    saved_path = viz.save_html(filename='results/custom_report.html', fig=fig)
    print(f"\n✅ График сохранен: {saved_path}")

    fig.show()


def example_dual_timeframe_visualization():
    """Пример визуализации для dual timeframe режима"""
    print("\n" + "="*70)
    print("ПРИМЕР 4: Визуализация Dual Timeframe бэктеста")
    print("="*70 + "\n")

    # Конфигурация для dual timeframe
    config_dual = {
        "start_balance": 1000,
        "leverage": 1,
        "order_type": "long",
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "execution_timeframe": "1m",
        "entry_conditions": {
            "type": "manual",
            "trigger": "price_drop",
            "percent": 2
        },
        "first_order": {
            "amount_percent": 10
        },
        "dca": {
            "enabled": True,
            "max_orders": 3,
            "martingale": {
                "enabled": True,
                "multiplier": 2.0
            },
            "step_price": {
                "type": "fixed_percent",
                "value": 1.5
            }
        },
        "take_profit": {
            "enabled": True,
            "percent": 3
        },
        "stop_loss": {
            "enabled": True,
            "percent": 5
        },
        "risk_management": {
            "max_drawdown_percent": 20,
            "max_open_positions": 1
        },
        "data_source": {
            "type": "api",
            "api": {
                "exchange": "binance",
                "symbol": "BTC/USDT",
                "auto_save": False,
                "market_type": "spot"
            }
        },
        "start_date": "2025-01-01",
        "end_date": "2025-01-07"
    }

    try:
        # Создаем бэктестер с dual timeframe
        bt = Backtester(config_dict=config_dual)

        # Запускаем бэктест
        print("⏳ Запуск dual timeframe бэктеста...")
        results = bt.run_backtest(verbose=False)

        # Визуализируем (будет использован execution timeframe для графика)
        fig = bt.visualize_results(
            graph_type='all',
            save_html=True,
            filename='results/dual_timeframe_report.html'
        )

        print("\n✅ Dual timeframe визуализация завершена")
        fig.show()

    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        print("Примечание: Для dual timeframe нужен доступ к API биржи")


if __name__ == "__main__":
    # Выберите пример для запуска:

    # Пример 1: Все графики в одном окне
    example_basic_visualization()

    # Пример 2: Отдельные графики (раскомментируйте для запуска)
    # example_individual_charts()

    # Пример 3: Прямое использование визуализатора (раскомментируйте для запуска)
    # example_with_direct_visualizer()

    # Пример 4: Dual timeframe (раскомментируйте для запуска, требуется API доступ)
    # example_dual_timeframe_visualization()

    print("\n" + "="*70)
    print("✨ Визуализация завершена!")
    print("="*70)
    print("\n💡 Совет: Откройте HTML файлы в браузере для интерактивного просмотра")
    print("   Все графики сохранены в папке 'results/'\n")
