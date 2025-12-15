#!/usr/bin/env python3
"""
Тестирование визуализации индикаторов
"""

from backtester import Backtester

print("\n" + "="*70)
print("ТЕСТ ВИЗУАЛИЗАЦИИ ИНДИКАТОРОВ")
print("="*70 + "\n")

# Создаем бэктестер с индикаторной стратегией
bt = Backtester(config_path='test_config_indicators.json')

# Запускаем бэктест
print("⏳ Запуск бэктеста...")
results = bt.run_backtest(verbose=False)

print(f"✅ Бэктест завершен")
print(f"   Сделок: {results['basic_stats']['total_trades']}")
print(f"   Win Rate: {results['basic_stats']['win_rate']:.2f}%")

# Визуализируем с индикаторами
print("\n📊 Создание графика с индикаторами...")
fig = bt.visualize_results(
    graph_type='price',
    show_indicators=True,  # <- Включаем индикаторы!
    show_dca=True,
    save_html=True,
    filename='results/backtest_with_indicators.html'
)

print("\n✅ График сохранен: results/backtest_with_indicators.html")
print("\n💡 Откройте файл в браузере чтобы увидеть:")
print("   - Свечной график цены")
print("   - Линии EMA 50 и EMA 200")
print("   - График RSI с уровнями 30/70")
print("   - Метки входов и выходов")

print("\n" + "="*70)
print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
print("="*70 + "\n")
