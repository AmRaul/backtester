#!/usr/bin/env python3
"""
Веб-интерфейс для бэктестера алгоритмических стратегий
"""

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
import json
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path
import base64
import io

from backtester import Backtester
from reporter import BacktestReporter
from data_loader import DataLoader

app = Flask(__name__)
app.secret_key = 'backtester_secret_key_change_in_production'

# Глобальные переменные для отслеживания задач
running_backtests = {}
backtest_results = {}

class BacktestTask:
    def __init__(self, task_id, config):
        self.task_id = task_id
        self.config = config
        self.status = 'pending'
        self.progress = 0
        self.results = None
        self.error = None
        self.start_time = datetime.now()

def run_backtest_async(task_id, config):
    """Запускает бэктест в отдельном потоке"""
    task = running_backtests[task_id]
    
    try:
        task.status = 'running'
        
        # Создаем бэктестер
        backtester = Backtester(config_dict=config)
        
        # Запускаем бэктест
        results = backtester.run_backtest(verbose=False)
        
        # Сохраняем результаты
        task.results = results
        task.status = 'completed'
        task.progress = 100
        
        # Сохраняем в глобальный кэш
        backtest_results[task_id] = results
        
    except Exception as e:
        task.error = str(e)
        task.status = 'error'
        print(f"Ошибка в бэктесте {task_id}: {e}")

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/config')
def config_page():
    """Страница конфигурации"""
    # Загружаем примеры конфигураций
    examples = {}
    
    # CSV примеры
    if os.path.exists('config_examples.json'):
        with open('config_examples.json', 'r', encoding='utf-8') as f:
            examples['csv'] = json.load(f)
    
    # API примеры
    if os.path.exists('config_api_examples.json'):
        with open('config_api_examples.json', 'r', encoding='utf-8') as f:
            examples['api'] = json.load(f)
    
    # Получаем список доступных бирж
    loader = DataLoader()
    exchanges = loader.get_available_exchanges()
    
    return render_template('config.html', examples=examples, exchanges=exchanges)

@app.route('/api/exchanges')
def get_exchanges():
    """API для получения списка бирж"""
    loader = DataLoader()
    exchanges = loader.get_available_exchanges()
    return jsonify(exchanges)

@app.route('/api/exchange-info/<exchange>')
def get_exchange_info(exchange):
    """API для получения информации о бирже"""
    loader = DataLoader()
    info = loader.get_exchange_info(exchange)
    return jsonify(info)

@app.route('/api/run-backtest', methods=['POST'])
def run_backtest():
    """API для запуска бэктеста"""
    try:
        config = request.json
        
        if not config:
            return jsonify({'error': 'Не предоставлена конфигурация'}), 400
        
        # Генерируем уникальный ID задачи
        task_id = str(uuid.uuid4())
        
        # Создаем задачу
        task = BacktestTask(task_id, config)
        running_backtests[task_id] = task
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=run_backtest_async, args=(task_id, config))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'status': 'started',
            'message': 'Бэктест запущен'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest-status/<task_id>')
def get_backtest_status(task_id):
    """API для получения статуса бэктеста"""
    if task_id not in running_backtests:
        return jsonify({'error': 'Задача не найдена'}), 404
    
    task = running_backtests[task_id]
    
    response = {
        'task_id': task_id,
        'status': task.status,
        'progress': task.progress,
        'start_time': task.start_time.isoformat()
    }
    
    if task.error:
        response['error'] = task.error
    
    if task.results:
        # Добавляем основные результаты
        stats = task.results.get('basic_stats', {})
        response['results_summary'] = {
            'total_trades': stats.get('total_trades', 0),
            'win_rate': stats.get('win_rate', 0),
            'total_return': stats.get('total_return', 0),
            'final_balance': stats.get('current_balance', 0)
        }
    
    return jsonify(response)

@app.route('/api/backtest-results/<task_id>')
def get_backtest_results(task_id):
    """API для получения полных результатов бэктеста"""
    if task_id not in backtest_results:
        return jsonify({'error': 'Результаты не найдены'}), 404
    
    results = backtest_results[task_id]
    
    # Подготавливаем результаты для JSON
    json_results = prepare_results_for_json(results)
    
    return jsonify(json_results)

@app.route('/api/download-data', methods=['POST'])
def download_data():
    """API для загрузки данных с биржи"""
    try:
        params = request.json
        
        exchange = params.get('exchange', 'binance')
        symbol = params.get('symbol', 'BTC/USDT')
        timeframe = params.get('timeframe', '1h')
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        
        loader = DataLoader()
        
        # Загружаем данные
        data = loader.load_from_api(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            exchange=exchange
        )
        
        # Сохраняем в CSV
        filename = loader.save_to_csv()
        
        return jsonify({
            'success': True,
            'message': f'Данные загружены и сохранены в {filename}',
            'filename': filename,
            'records_count': len(data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/results')
def results_page():
    """Страница результатов"""
    # Получаем список завершенных бэктестов
    completed_tasks = []
    for task_id, task in running_backtests.items():
        if task.status in ['completed', 'error']:
            completed_tasks.append({
                'task_id': task_id,
                'status': task.status,
                'start_time': task.start_time,
                'config_symbol': task.config.get('symbol', 'Unknown')
            })
    
    return render_template('results.html', tasks=completed_tasks)

@app.route('/results/<task_id>')
def view_results(task_id):
    """Просмотр детальных результатов"""
    if task_id not in backtest_results:
        flash('Результаты не найдены', 'error')
        return redirect(url_for('results_page'))
    
    results = backtest_results[task_id]
    
    # Создаем репортер для генерации графиков
    reporter = BacktestReporter(results)
    
    # Генерируем графики в base64 для встраивания в HTML
    charts = generate_charts_base64(reporter)
    
    return render_template('view_results.html', 
                         results=results, 
                         task_id=task_id,
                         charts=charts)

@app.route('/api/generate-report/<task_id>')
def generate_report(task_id):
    """Генерирует полный отчет"""
    if task_id not in backtest_results:
        return jsonify({'error': 'Результаты не найдены'}), 404
    
    try:
        results = backtest_results[task_id]
        reporter = BacktestReporter(results)
        
        # Генерируем отчет в директории reports
        output_dir = f"reports/report_{task_id}"
        reporter.generate_full_report(output_dir)
        
        return jsonify({
            'success': True,
            'message': f'Отчет сгенерирован в {output_dir}',
            'report_dir': output_dir
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def prepare_results_for_json(results):
    """Подготавливает результаты для JSON сериализации"""
    def convert_for_json(obj):
        if hasattr(obj, 'isoformat'):  # datetime
            return obj.isoformat()
        elif hasattr(obj, 'item'):  # numpy types
            return obj.item()
        elif isinstance(obj, dict):
            return {key: convert_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_for_json(item) for item in obj]
        else:
            return obj
    
    return convert_for_json(results)

def generate_charts_base64(reporter):
    """Генерирует графики в формате base64"""
    charts = {}
    
    try:
        import matplotlib
        matplotlib.use('Agg')  # Используем backend без GUI
        import matplotlib.pyplot as plt
        
        # График эквити
        if reporter.balance_history:
            plt.figure(figsize=(10, 6))
            reporter.create_equity_curve_plot(show=False)
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight')
            img_buffer.seek(0)
            
            charts['equity_curve'] = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()
        
        # График распределения PnL
        if reporter.trade_history:
            plt.figure(figsize=(10, 6))
            reporter.create_pnl_distribution_plot(show=False)
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight')
            img_buffer.seek(0)
            
            charts['pnl_distribution'] = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()
            
    except Exception as e:
        print(f"Ошибка генерации графиков: {e}")
    
    return charts

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="Страница не найдена"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Внутренняя ошибка сервера"), 500

if __name__ == '__main__':
    # Создаем необходимые директории
    os.makedirs('data', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(host='0.0.0.0', port=8000, debug=True) 