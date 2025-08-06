#!/usr/bin/env python3
"""
Скрипт для детальной проверки расчетов бэктестера
"""

import json
import pandas as pd
from datetime import datetime

def verify_calculations(results_file):
    """
    Проверяет все расчеты в результатах бэктестера
    
    Args:
        results_file: путь к JSON файлу с результатами
    """
    print("🔍 ПРОВЕРКА РАСЧЕТОВ БЭКТЕСТЕРА")
    print("=" * 60)
    
    # Загружаем результаты
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Получаем данные
    basic_stats = results['basic_stats']
    trade_history = results['trade_history']
    
    print(f"📊 ОСНОВНЫЕ ДАННЫЕ:")
    print(f"Начальный баланс: ${basic_stats.get('current_balance', 0):,.2f}")
    print(f"Всего сделок: {len(trade_history)}")
    
    # Разделяем сделки
    completed_trades = [t for t in trade_history if t['reason'] != 'end_of_data']
    open_trades = [t for t in trade_history if t['reason'] == 'end_of_data']
    
    print(f"Завершенных сделок: {len(completed_trades)}")
    print(f"Незавершенных сделок: {len(open_trades)}")
    print()
    
    # Проверяем завершенные сделки
    if completed_trades:
        print("✅ ПРОВЕРКА ЗАВЕРШЕННЫХ СДЕЛОК:")
        print("-" * 40)
        
        total_pnl = 0
        winning_trades = 0
        losing_trades = 0
        
        for i, trade in enumerate(completed_trades, 1):
            pnl = trade['pnl']
            total_pnl += pnl
            
            if pnl > 0:
                winning_trades += 1
            else:
                losing_trades += 1
            
            print(f"{i:2d}. {trade['symbol']} | "
                  f"Вход: ${trade['entry_price']:.4f} | "
                  f"Средняя: ${trade.get('average_price', trade['entry_price']):.4f} | "
                  f"Выход: ${trade['exit_price']:.4f} | "
                  f"PnL: ${pnl:.2f} ({trade['pnl_percent']:.2f}%) | "
                  f"DCA: {trade['dca_orders_count']}")
        
        print()
        print(f"📈 СВОДКА ПО ЗАВЕРШЕННЫМ СДЕЛКАМ:")
        print(f"Общий PnL: ${total_pnl:.2f}")
        print(f"Прибыльных: {winning_trades}")
        print(f"Убыточных: {losing_trades}")
        print(f"Win Rate: {winning_trades/len(completed_trades)*100:.1f}%")
        
        # Проверяем баланс
        initial_balance = 2000  # Предполагаем
        calculated_balance = initial_balance + total_pnl
        reported_balance = basic_stats.get('current_balance', 0)
        
        print()
        print(f"💰 ПРОВЕРКА БАЛАНСА:")
        print(f"Начальный баланс: ${initial_balance:,.2f}")
        print(f"Общий PnL: ${total_pnl:.2f}")
        print(f"Рассчитанный баланс: ${calculated_balance:,.2f}")
        print(f"Заявленный баланс: ${reported_balance:,.2f}")
        
        if abs(calculated_balance - reported_balance) < 0.01:
            print("✅ БАЛАНС РАССЧИТАН ПРАВИЛЬНО")
        else:
            print("❌ ОШИБКА В РАСЧЕТЕ БАЛАНСА")
            print(f"Разница: ${calculated_balance - reported_balance:.2f}")
    
    # Проверяем незавершенные сделки
    if open_trades:
        print()
        print("⚠️  НЕЗАВЕРШЕННЫЕ СДЕЛКИ:")
        print("-" * 40)
        
        total_invested = 0
        unrealized_pnl = 0
        
        for i, trade in enumerate(open_trades, 1):
            # Рассчитываем вложенные средства
            avg_price = trade.get('average_price', trade['entry_price'])
            invested = avg_price * trade['quantity']
            total_invested += invested
            
            # Рассчитываем нереализованный PnL
            current_value = trade['exit_price'] * trade['quantity']
            unrealized = current_value - invested
            unrealized_pnl += unrealized
            
            print(f"{i:2d}. {trade['symbol']} | "
                  f"Вход: ${trade['entry_price']:.4f} | "
                  f"Средняя: ${avg_price:.4f} | "
                  f"Текущая цена: ${trade['exit_price']:.4f} | "
                  f"Вложено: ${invested:.2f} | "
                  f"Нереализованный PnL: ${unrealized:.2f} | "
                  f"DCA: {trade['dca_orders_count']}")
        
        print()
        print(f"📊 СВОДКА ПО НЕЗАВЕРШЕННЫМ СДЕЛКАМ:")
        print(f"Всего вложено: ${total_invested:.2f}")
        print(f"Нереализованный PnL: ${unrealized_pnl:.2f}")
        
        # Проверяем реальный баланс
        if 'actual_balance' in basic_stats:
            actual_balance = basic_stats['actual_balance']
            expected_balance = initial_balance + total_pnl + unrealized_pnl
            
            print()
            print(f"💰 ПРОВЕРКА РЕАЛЬНОГО БАЛАНСА:")
            print(f"Баланс завершенных сделок: ${initial_balance + total_pnl:,.2f}")
            print(f"Нереализованный PnL: ${unrealized_pnl:.2f}")
            print(f"Ожидаемый реальный баланс: ${expected_balance:,.2f}")
            print(f"Заявленный реальный баланс: ${actual_balance:,.2f}")
            
            if abs(expected_balance - actual_balance) < 0.01:
                print("✅ РЕАЛЬНЫЙ БАЛАНС РАССЧИТАН ПРАВИЛЬНО")
            else:
                print("❌ ОШИБКА В РАСЧЕТЕ РЕАЛЬНОГО БАЛАНСА")
                print(f"Разница: ${expected_balance - actual_balance:.2f}")
    
    print()
    print("=" * 60)
    print("🔍 ПРОВЕРКА ЗАВЕРШЕНА")

if __name__ == "__main__":
    import sys
    import os
    
    if len(sys.argv) != 2:
        print("Использование: python debug_calculations.py <results_file.json>")
        print("Примеры:")
        print("  python debug_calculations.py results/backtest_results_20250101_120000.json")
        print("  python debug_calculations.py backtest_results_20250101_120000.json")
        print("\nДоступные файлы в results/:")
        if os.path.exists('results'):
            files = [f for f in os.listdir('results') if f.endswith('.json')]
            if files:
                for file in sorted(files, reverse=True)[:5]:  # Показываем последние 5 файлов
                    print(f"  {file}")
            else:
                print("  (нет файлов)")
        sys.exit(1)
    
    results_file = sys.argv[1]
    
    # Если файл не найден, попробуем найти в директории results
    if not os.path.exists(results_file):
        results_file_in_dir = os.path.join('results', results_file)
        if os.path.exists(results_file_in_dir):
            results_file = results_file_in_dir
        else:
            print(f"❌ Файл не найден: {results_file}")
            print(f"❌ Также не найден: {results_file_in_dir}")
            sys.exit(1)
    
    verify_calculations(results_file) 