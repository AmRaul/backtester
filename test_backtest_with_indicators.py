#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы индикаторов в бэктесте
"""

from backtester import Backtester
import json

def test_backtest_with_indicators():
    """Запускает бэктест с индикаторной стратегией"""
    print("\n" + "="*70)
    print("ТЕСТ БЭКТЕСТА С ИНДИКАТОРАМИ (EMA + RSI)")
    print("="*70 + "\n")

    try:
        # Создаем бэктестер с конфигурацией индикаторов
        bt = Backtester(config_path='test_config_indicators.json')

        print("📊 Конфигурация загружена")
        print(f"   Стратегия: {bt.config['indicators']['strategy_type']}")
        print(f"   EMA Short: {bt.config['indicators']['trend_momentum']['ema_short']}")
        print(f"   EMA Long: {bt.config['indicators']['trend_momentum']['ema_long']}")
        print(f"   RSI Period: {bt.config['indicators']['trend_momentum']['rsi_period']}")
        print(f"   Символ: {bt.config['symbol']}")
        print(f"   Таймфрейм: {bt.config['timeframe']}")

        # Загружаем данные
        print("\n📥 Загрузка данных...")
        data = bt.load_data()
        print(f"   Загружено {len(data)} свечей")
        print(f"   Период: {data.index[0]} - {data.index[-1]}")

        # Запускаем бэктест с подробным выводом
        print("\n🚀 Запуск бэктеста...\n")
        results = bt.run_backtest(verbose=True)

        # Выводим результаты
        print("\n" + "="*70)
        print("РЕЗУЛЬТАТЫ БЭКТЕСТА")
        print("="*70)

        stats = results.get('basic_stats', {})

        print(f"\n💰 Финансовые показатели:")
        print(f"   Начальный баланс: ${stats.get('initial_balance', 0):.2f}")
        print(f"   Конечный баланс: ${stats.get('final_balance', 0):.2f}")
        print(f"   Общая прибыль: ${stats.get('total_pnl', 0):.2f}")
        print(f"   Прибыль %: {stats.get('total_return_percent', 0):.2f}%")

        print(f"\n📈 Статистика сделок:")
        print(f"   Всего сделок: {stats.get('total_trades', 0)}")
        print(f"   Прибыльных: {stats.get('winning_trades', 0)}")
        print(f"   Убыточных: {stats.get('losing_trades', 0)}")
        print(f"   Win Rate: {stats.get('win_rate', 0):.2f}%")

        print(f"\n📊 Риск-метрики:")
        print(f"   Максимальная просадка: {stats.get('max_drawdown_percent', 0):.2f}%")
        print(f"   Средняя прибыль: ${stats.get('avg_profit', 0):.2f}")
        print(f"   Средний убыток: ${stats.get('avg_loss', 0):.2f}")

        adv_metrics = results.get('advanced_metrics', {})
        print(f"\n📐 Продвинутые метрики:")
        print(f"   Sharpe Ratio: {adv_metrics.get('sharpe_ratio', 0):.2f}")
        print(f"   Sortino Ratio: {adv_metrics.get('sortino_ratio', 0):.2f}")
        print(f"   Calmar Ratio: {adv_metrics.get('calmar_ratio', 0):.2f}")
        print(f"   Profit Factor: {adv_metrics.get('profit_factor', 0):.2f}")

        # Выводим информацию о первых сделках
        trades = results.get('trade_history', [])
        if trades:
            print(f"\n📝 Первые 3 сделки:")
            for i, trade in enumerate(trades[:3], 1):
                print(f"\n   Сделка {i}:")
                print(f"      Вход: {trade['entry_time']} @ ${trade['entry_price']:.4f}")
                print(f"      Выход: {trade['exit_time']} @ ${trade['exit_price']:.4f}")
                print(f"      PnL: ${trade['pnl']:.2f} ({trade['pnl_percent']:.2f}%)")
                print(f"      Причина выхода: {trade['reason']}")

        print("\n" + "="*70)
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print("="*70 + "\n")

        return results

    except FileNotFoundError as e:
        print(f"\n❌ Ошибка: Файл данных не найден")
        print(f"   {e}")
        print(f"\n💡 Убедитесь что файл data/XRPUSDT_15m_20250806_003529.csv существует")
        return None

    except Exception as e:
        print(f"\n❌ Ошибка при выполнении бэктеста:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_backtest_with_indicators()
