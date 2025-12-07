#!/usr/bin/env python3
"""
Тестовый скрипт для демонстрации Dual Timeframe бэктестинга

Использование:
    python test_dual_timeframe.py
"""

from backtester import Backtester
import json

def test_dual_timeframe():
    """Тестирует dual timeframe режим"""

    print("="*70)
    print("DUAL TIMEFRAME BACKTESTING TEST")
    print("="*70)
    print()

    # Загружаем конфиг
    with open('config_dual_timeframe_example.json', 'r') as f:
        configs = json.load(f)

    # Выбираем конфиг для теста
    config_name = 'dual_tf_btc_15m_1m'
    config = configs[config_name]

    print(f"Запуск бэктеста с конфигурацией: {config_name}")
    print(f"Strategy TF: {config['timeframe']}")
    print(f"Execution TF: {config['execution_timeframe']}")
    print(f"Period: {config['start_date']} - {config['end_date']}")
    print()

    # Создаем бэктестер
    bt = Backtester(config_dict=config)

    # Запускаем бэктест
    results = bt.run_backtest(verbose=True)

    # Сохраняем результаты
    saved_file = bt.save_results(filename=f"{config_name}_results.json")
    print(f"\n✅ Результаты сохранены в: {saved_file}")

    return results


def test_single_vs_dual():
    """Сравнивает single и dual timeframe режимы"""

    print("\n" + "="*70)
    print("СРАВНЕНИЕ SINGLE vs DUAL TIMEFRAME")
    print("="*70)
    print()

    with open('config_dual_timeframe_example.json', 'r') as f:
        configs = json.load(f)

    # Dual timeframe тест
    print("1️⃣  DUAL TIMEFRAME MODE (1m execution / 15m strategy)")
    print("-" * 70)
    dual_config = configs['dual_tf_btc_15m_1m'].copy()
    bt_dual = Backtester(config_dict=dual_config)
    results_dual = bt_dual.run_backtest(verbose=False)

    print("\n" + "="*70)

    # Single timeframe тест (убираем execution_timeframe)
    print("2️⃣  SINGLE TIMEFRAME MODE (15m only)")
    print("-" * 70)
    single_config = dual_config.copy()
    single_config.pop('execution_timeframe', None)  # Удаляем execution_timeframe
    bt_single = Backtester(config_dict=single_config)
    results_single = bt_single.run_backtest(verbose=False)

    # Сравнение результатов
    print("\n" + "="*70)
    print("📊 СРАВНЕНИЕ РЕЗУЛЬТАТОВ")
    print("="*70)

    print(f"\n{'Метрика':<30} {'Single TF':>15} {'Dual TF':>15} {'Разница':>15}")
    print("-" * 78)

    # Основные метрики
    metrics = [
        ('Всего сделок', 'total_trades'),
        ('Win Rate %', 'win_rate'),
        ('Общий PnL $', 'total_pnl'),
        ('Средний PnL $', 'average_pnl'),
        ('Макс прибыль $', 'max_profit'),
        ('Макс убыток $', 'max_loss'),
    ]

    for label, key in metrics:
        single_val = results_single['basic_stats'][key]
        dual_val = results_dual['basic_stats'][key]
        diff = dual_val - single_val

        if key == 'total_trades':
            print(f"{label:<30} {single_val:>15.0f} {dual_val:>15.0f} {diff:>+15.0f}")
        else:
            print(f"{label:<30} {single_val:>15.2f} {dual_val:>15.2f} {diff:>+15.2f}")

    print("\n" + "="*70)
    print("✅ Тест завершен!")
    print("="*70)


if __name__ == "__main__":
    # Запускаем тест dual timeframe
    try:
        results = test_dual_timeframe()

        # Опционально: сравнение режимов (закомментировано чтобы не перегружать)
        # test_single_vs_dual()

    except Exception as e:
        print(f"\n❌ Ошибка при выполнении теста: {e}")
        import traceback
        traceback.print_exc()
