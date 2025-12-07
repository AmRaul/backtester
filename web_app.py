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
import sqlite3
from contextlib import contextmanager
import pandas as pd

from backtester import Backtester
from reporter import BacktestReporter
from data_loader import DataLoader
from visualizer import BacktestVisualizer

app = Flask(__name__)
app.secret_key = 'backtester_secret_key_change_in_production'

# Глобальные переменные для отслеживания задач
running_backtests = {}
backtest_results = {}

# Инициализация базы данных
def init_database():
    """Инициализирует базу данных SQLite"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Таблица для сохранения конфигураций стратегий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                config_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_public BOOLEAN DEFAULT 0,
                author TEXT DEFAULT 'user',
                tags TEXT,
                performance_score REAL DEFAULT 0.0
            )
        ''')
        
        # Таблица для истории бэктестов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                symbol TEXT,
                timeframe TEXT,
                config_name TEXT,
                config_json TEXT NOT NULL,
                results_json TEXT,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                total_trades INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0.0,
                total_return REAL DEFAULT 0.0,
                max_drawdown REAL DEFAULT 0.0,
                sharpe_ratio REAL DEFAULT 0.0
            )
        ''')
        
        conn.commit()

@contextmanager
def get_db_connection():
    """Контекстный менеджер для работы с базой данных"""
    import os
    db_dir = 'db'
    db_path = os.path.join(db_dir, 'backtester.db')

    # Создаем директорию если её нет
    os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
    try:
        yield conn
    finally:
        conn.close()

# Инициализируем базу данных при импорте модуля
init_database()

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

        # Сохраняем в глобальный кэш (для быстрого доступа)
        backtest_results[task_id] = results

        # Сохраняем в базу данных (для постоянного хранения)
        try:
            save_backtest_to_db(task_id, config, results)
            print(f"[BACKTEST] Результаты {task_id} сохранены в БД")
        except Exception as db_error:
            print(f"[BACKTEST ERROR] Не удалось сохранить в БД: {db_error}")

    except Exception as e:
        task.error = str(e)
        task.status = 'error'
        print(f"Ошибка в бэктесте {task_id}: {e}")

def save_backtest_to_db(task_id, config, results):
    """Сохраняет результаты бэктеста в базу данных"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Подготавливаем данные для сохранения
        config_json = json.dumps(config)
        results_json = json.dumps(prepare_results_for_json(results))

        # Извлекаем основные метрики
        symbol = config.get('symbol', 'Unknown')
        timeframe = config.get('timeframe', 'Unknown')
        total_return = results.get('basic_stats', {}).get('total_return', 0)
        total_trades = results.get('basic_stats', {}).get('total_trades', 0)
        win_rate = results.get('basic_stats', {}).get('win_rate', 0)

        cursor.execute('''
            INSERT INTO backtest_history
            (task_id, config_name, config_json, results_json, status,
             symbol, timeframe, total_return, total_trades, win_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_id,
            f"{symbol}_{timeframe}",
            config_json,
            results_json,
            'completed',
            symbol,
            timeframe,
            total_return,
            total_trades,
            win_rate
        ))

        conn.commit()

def load_backtest_from_db(task_id):
    """Загружает результаты бэктеста из базы данных"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT results_json FROM backtest_history
                WHERE task_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (task_id,))

            row = cursor.fetchone()
            if row:
                results_json = row['results_json']
                return json.loads(results_json)
            return None
    except Exception as e:
        print(f"[DB ERROR] Ошибка загрузки из БД: {e}")
        return None

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
    try:
        loader = DataLoader()
        exchanges = loader.get_available_exchanges()
    except Exception as e:
        print(f"Ошибка загрузки бирж: {e}")
        exchanges = ['binance', 'okx', 'bybit', 'kucoin']  # Fallback список

    # Получаем список CSV файлов из директории data/ с метаданными
    csv_files = []
    data_dir = Path('data')
    if data_dir.exists():
        for csv_file in data_dir.glob('*.csv'):
            try:
                df = pd.read_csv(csv_file)
                rows_count = len(df)
                date_range = None
                if 'timestamp' in df.columns and len(df) > 0:
                    start_date = pd.to_datetime(df['timestamp'].iloc[0]).strftime('%Y-%m-%d')
                    end_date = pd.to_datetime(df['timestamp'].iloc[-1]).strftime('%Y-%m-%d')
                    date_range = f"{start_date} - {end_date}"

                csv_files.append({
                    'path': str(csv_file),
                    'name': csv_file.name,
                    'date_range': date_range,
                    'rows': rows_count,
                    'size': csv_file.stat().st_size
                })
            except Exception as e:
                # Если не удается прочитать, добавляем без метаданных
                csv_files.append({
                    'path': str(csv_file),
                    'name': csv_file.name,
                    'date_range': None,
                    'rows': 0,
                    'size': csv_file.stat().st_size if csv_file.exists() else 0
                })
        # Сортируем по дате изменения
        csv_files.sort(key=lambda x: Path(x['path']).stat().st_mtime, reverse=True)

    return render_template('config.html', examples=examples, exchanges=exchanges, csv_files=csv_files)

@app.route('/api/csv-files')
def get_csv_files():
    """API для получения списка CSV файлов"""
    try:
        csv_files = []
        data_dir = Path('data')
        if data_dir.exists():
            for csv_file in data_dir.glob('*.csv'):
                file_stat = csv_file.stat()

                # Читаем первую и последнюю строку для определения диапазона дат
                date_range = None
                rows_count = 0
                try:
                    df = pd.read_csv(csv_file)
                    rows_count = len(df)
                    if 'timestamp' in df.columns and len(df) > 0:
                        start_date = pd.to_datetime(df['timestamp'].iloc[0]).strftime('%Y-%m-%d')
                        end_date = pd.to_datetime(df['timestamp'].iloc[-1]).strftime('%Y-%m-%d')
                        date_range = f"{start_date} - {end_date}"
                except Exception as e:
                    print(f"Ошибка чтения {csv_file}: {e}")

                csv_files.append({
                    'path': str(csv_file),
                    'name': csv_file.name,
                    'size': file_stat.st_size,
                    'modified': file_stat.st_mtime,
                    'date_range': date_range,
                    'rows': rows_count
                })
        # Сортируем по дате изменения (новые первыми)
        csv_files.sort(key=lambda x: x['modified'], reverse=True)
        return jsonify({'files': csv_files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        market_type = params.get('market_type', 'spot')

        # Обработка периода или кастомных дат
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        period = params.get('period')

        # Если указан период, рассчитываем даты
        if period and not (start_date and end_date):
            from datetime import datetime, timedelta
            end_date_obj = datetime.now()

            period_days = {
                '1m': 30,
                '3m': 90,
                '6m': 180,
                '1y': 365,
                'all': None  # Для "все время" не указываем start_date
            }

            days = period_days.get(period)
            if days:
                start_date_obj = end_date_obj - timedelta(days=days)
                start_date = start_date_obj.strftime('%Y-%m-%d')
                end_date = end_date_obj.strftime('%Y-%m-%d')
            else:
                # Для "all" не передаем start_date
                start_date = None
                end_date = None

        loader = DataLoader()

        # Загружаем данные
        data = loader.load_from_api(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            exchange=exchange,
            market_type=market_type
        )

        # Сохраняем в CSV
        filename = loader.save_to_csv()

        return jsonify({
            'success': True,
            'message': f'Данные загружены и сохранены в {filename}',
            'filename': filename,
            'records_count': len(data),
            'market_type': market_type,
            'period': period if period else 'custom'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/current-price', methods=['POST'])
def get_current_price():
    """Получить текущую цену с биржи"""
    try:
        params = request.json
        exchange_name = params.get('exchange', 'binance')
        symbol = params.get('symbol', 'BTC/USDT')
        market_type = params.get('market_type', 'spot')

        print(f"[PRICE API] Запрос цены: exchange={exchange_name}, symbol={symbol}, market_type={market_type}")

        # Формируем символ в зависимости от типа рынка
        full_symbol = symbol
        if market_type in ['futures', 'swap']:
            if ':' not in symbol:
                if '/USDT' in symbol:
                    full_symbol = symbol + ':USDT'

        print(f"[PRICE API] Полный символ: {full_symbol}")

        # Загружаем exchange
        import ccxt
        exchange_class = getattr(ccxt, exchange_name)
        exchange = exchange_class()

        # Загружаем рынки
        print(f"[PRICE API] Загрузка рынков с {exchange_name}...")
        exchange.load_markets()

        # Проверяем наличие символа
        if full_symbol not in exchange.markets:
            available_symbols = [s for s in exchange.markets.keys() if 'USDT' in s and symbol.split('/')[0] in s]
            error_msg = f"Символ {full_symbol} не найден на {exchange_name}."
            if available_symbols:
                error_msg += f" Возможные варианты: {', '.join(available_symbols[:5])}"
            print(f"[PRICE API ERROR] {error_msg}")
            return jsonify({'error': error_msg}), 404

        # Получаем тикер
        print(f"[PRICE API] Получение тикера для {full_symbol}...")
        ticker = exchange.fetch_ticker(full_symbol)
        current_price = ticker['last']

        print(f"[PRICE API] Успешно получена цена: {current_price}")

        return jsonify({
            'success': True,
            'price': current_price,
            'symbol': full_symbol,
            'bid': ticker.get('bid'),
            'ask': ticker.get('ask'),
            'volume': ticker.get('baseVolume'),
            'timestamp': ticker.get('timestamp')
        })

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[PRICE API ERROR] Ошибка получения цены:")
        print(error_trace)
        return jsonify({'error': str(e), 'trace': error_trace if app.debug else None}), 500

@app.route('/results')
def results_page():
    """Страница результатов"""
    # Получаем список всех задач
    all_tasks = []

    # Добавляем запущенные задачи
    for task_id, task in running_backtests.items():
        all_tasks.append({
            'task_id': task_id,
            'status': task.status,
            'start_time': task.start_time,
            'config_symbol': task.config.get('symbol', 'Unknown')
        })

    # Добавляем завершенные задачи из БД
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT task_id, symbol, timeframe, created_at, total_return, total_trades
                FROM backtest_history
                ORDER BY created_at DESC
                LIMIT 50
            ''')
            for row in cursor.fetchall():
                # Проверяем, не добавили ли мы уже эту задачу из running_backtests
                if not any(t['task_id'] == row['task_id'] for t in all_tasks):
                    # Конвертируем строку даты в datetime объект или оставляем как строку
                    from datetime import datetime
                    start_time = row['created_at']
                    try:
                        if start_time and isinstance(start_time, str):
                            # Пытаемся распарсить как ISO формат
                            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        # Если не получилось, оставляем как строку
                        pass

                    all_tasks.append({
                        'task_id': row['task_id'],
                        'status': 'completed',
                        'start_time': start_time,
                        'config_symbol': row['symbol'],
                        'total_return': row['total_return'],
                        'total_trades': row['total_trades']
                    })
    except Exception as e:
        print(f"[RESULTS PAGE] Ошибка загрузки из БД: {e}")

    return render_template('results.html', tasks=all_tasks)

@app.route('/results/<task_id>')
def view_results(task_id):
    """Просмотр детальных результатов"""
    # Сначала проверяем в кэше (памяти)
    if task_id in backtest_results:
        results = backtest_results[task_id]
    else:
        # Если нет в памяти, загружаем из БД
        results = load_backtest_from_db(task_id)
        if not results:
            flash('Результаты не найдены', 'error')
            return redirect(url_for('results_page'))
        # Кэшируем для быстрого доступа
        backtest_results[task_id] = results
    
    # Создаем репортер для генерации графиков
    try:
        reporter = BacktestReporter(results)
        # Генерируем графики в base64 для встраивания в HTML
        charts = generate_charts_base64(reporter)
    except Exception as e:
        print(f"Ошибка генерации графиков: {e}")
        charts = {}
    
    return render_template('view_results.html', 
                         results=results, 
                         task_id=task_id,
                         charts=charts)

@app.route('/strategies')
def strategies_page():
    """Страница управления стратегиями"""
    return render_template('strategies.html')

@app.route('/api/generate-report/<task_id>')
def generate_report(task_id):
    """Генерирует полный отчет"""
    # Сначала проверяем в кэше (памяти)
    if task_id in backtest_results:
        results = backtest_results[task_id]
    else:
        # Если нет в памяти, загружаем из БД
        results = load_backtest_from_db(task_id)
        if not results:
            return jsonify({'error': 'Результаты не найдены'}), 404
        # Кэшируем для быстрого доступа
        backtest_results[task_id] = results

    try:
        reporter = BacktestReporter(results)

        # Генерируем отчет в директории reports
        output_dir = f"reports/report_{task_id}"
        reporter.generate_full_report(output_dir)

        return jsonify({
            'success': True,
            'message': f'Отчет сгенерирован в {output_dir}',
            'report_dir': output_dir,
            'task_id': task_id
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-csv/<task_id>')
def download_csv(task_id):
    """Скачивание CSV файла со сделками"""
    try:
        # Ищем CSV файл для этого task_id
        report_dir = f"reports/report_{task_id}"
        if not os.path.exists(report_dir):
            return jsonify({'error': 'Отчет не найден. Сгенерируйте отчет сначала.'}), 404

        # Ищем CSV файл в директории
        csv_files = [f for f in os.listdir(report_dir) if f.endswith('.csv')]
        if not csv_files:
            return jsonify({'error': 'CSV файл не найден'}), 404

        csv_path = os.path.join(report_dir, csv_files[0])
        return send_file(csv_path,
                        as_attachment=True,
                        download_name=f'trades_{task_id[:8]}.csv',
                        mimetype='text/csv')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-json/<task_id>')
def download_json(task_id):
    """Скачивание JSON файла с полными результатами"""
    try:
        # Ищем JSON файл для этого task_id
        report_dir = f"reports/report_{task_id}"
        if not os.path.exists(report_dir):
            return jsonify({'error': 'Отчет не найден. Сгенерируйте отчет сначала.'}), 404

        # Ищем JSON файл в директории
        json_files = [f for f in os.listdir(report_dir) if f.endswith('.json')]
        if not json_files:
            return jsonify({'error': 'JSON файл не найден'}), 404

        json_path = os.path.join(report_dir, json_files[0])
        return send_file(json_path,
                        as_attachment=True,
                        download_name=f'results_{task_id[:8]}.json',
                        mimetype='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/report/<task_id>')
def view_report(task_id):
    """Просмотр сгенерированного отчета с графиками"""
    report_dir = f"reports/report_{task_id}"

    if not os.path.exists(report_dir):
        flash('Отчет не найден. Сгенерируйте отчет сначала.', 'error')
        return redirect(url_for('view_results', task_id=task_id))

    # Собираем все файлы отчета
    files = {
        'images': [],
        'csv': None,
        'json': None,
        'txt': None
    }

    for filename in os.listdir(report_dir):
        filepath = os.path.join(report_dir, filename)
        if filename.endswith('.png'):
            files['images'].append({
                'name': filename,
                'path': f'/api/report-image/{task_id}/{filename}'
            })
        elif filename.endswith('.csv'):
            files['csv'] = filename
        elif filename.endswith('.json'):
            files['json'] = filename
        elif filename.endswith('.txt'):
            files['txt'] = filename
            # Читаем текстовый отчет
            with open(filepath, 'r', encoding='utf-8') as f:
                files['txt_content'] = f.read()

    return render_template('report.html', task_id=task_id, files=files)

@app.route('/api/report-image/<task_id>/<filename>')
def get_report_image(task_id, filename):
    """Отдает изображение из отчета"""
    try:
        report_dir = f"reports/report_{task_id}"
        image_path = os.path.join(report_dir, filename)

        if not os.path.exists(image_path):
            return jsonify({'error': 'Изображение не найдено'}), 404

        return send_file(image_path, mimetype='image/png')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API для работы с конфигурациями стратегий
@app.route('/api/configs')
def get_configs():
    """Получить список сохраненных конфигураций"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, description, created_at, updated_at, 
                       is_public, author, tags, performance_score
                FROM strategy_configs 
                ORDER BY updated_at DESC
            ''')
            configs = [dict(row) for row in cursor.fetchall()]
            return jsonify(configs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/configs/<int:config_id>')
def get_config(config_id):
    """Получить конкретную конфигурацию"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM strategy_configs WHERE id = ?', (config_id,))
            config = cursor.fetchone()
            
            if not config:
                return jsonify({'error': 'Конфигурация не найдена'}), 404
            
            return jsonify(dict(config))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/configs', methods=['POST'])
def save_config():
    """Сохранить новую конфигурацию"""
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description', '')
        config_json = json.dumps(data.get('config'))
        is_public = data.get('is_public', False)
        author = data.get('author', 'user')
        tags = data.get('tags', '')
        
        if not name:
            return jsonify({'error': 'Название конфигурации обязательно'}), 400
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO strategy_configs 
                (name, description, config_json, is_public, author, tags)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, description, config_json, is_public, author, tags))
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'Конфигурация "{name}" сохранена',
                'id': cursor.lastrowid
            })
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Конфигурация с таким именем уже существует'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/configs/<int:config_id>', methods=['PUT'])
def update_config(config_id):
    """Обновить существующую конфигурацию"""
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description', '')
        config_json = json.dumps(data.get('config'))
        is_public = data.get('is_public', False)
        tags = data.get('tags', '')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE strategy_configs 
                SET name = ?, description = ?, config_json = ?, 
                    is_public = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (name, description, config_json, is_public, tags, config_id))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Конфигурация не найдена'}), 404
            
            conn.commit()
            return jsonify({'success': True, 'message': 'Конфигурация обновлена'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/configs/<int:config_id>', methods=['DELETE'])
def delete_config(config_id):
    """Удалить конфигурацию"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM strategy_configs WHERE id = ?', (config_id,))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Конфигурация не найдена'}), 404
            
            conn.commit()
            return jsonify({'success': True, 'message': 'Конфигурация удалена'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/configs/<int:config_id>/duplicate', methods=['POST'])
def duplicate_config(config_id):
    """Дублировать конфигурацию"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM strategy_configs WHERE id = ?', (config_id,))
            original = cursor.fetchone()
            
            if not original:
                return jsonify({'error': 'Конфигурация не найдена'}), 404
            
            # Создаем копию с новым именем
            new_name = f"{original['name']} (копия)"
            cursor.execute('''
                INSERT INTO strategy_configs 
                (name, description, config_json, is_public, author, tags)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (new_name, original['description'], original['config_json'], 
                  False, original['author'], original['tags']))
            
            conn.commit()
            return jsonify({
                'success': True,
                'message': f'Конфигурация скопирована как "{new_name}"',
                'id': cursor.lastrowid
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
        elif hasattr(obj, '__dict__'):  # Объекты классов (Trade, etc)
            return convert_for_json(obj.__dict__)
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

@app.route('/api/backtest/<task_id>', methods=['DELETE'])
def delete_backtest(task_id):
    """Удаляет бэктест из базы данных и файлы отчетов"""
    try:
        import shutil

        # Удаляем из памяти
        if task_id in running_backtests:
            del running_backtests[task_id]
        if task_id in backtest_results:
            del backtest_results[task_id]

        # Удаляем из базы данных
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM backtest_history WHERE task_id = ?', (task_id,))
            deleted_count = cursor.rowcount
            conn.commit()

        # Удаляем директорию с отчетами
        report_dir = f"reports/report_{task_id}"
        if os.path.exists(report_dir):
            shutil.rmtree(report_dir)
            print(f"[DELETE] Удалена директория отчета: {report_dir}")

        if deleted_count > 0:
            return jsonify({
                'success': True,
                'message': 'Бэктест успешно удален'
            })
        else:
            return jsonify({'error': 'Бэктест не найден'}), 404

    except Exception as e:
        print(f"[DELETE ERROR] Ошибка удаления бэктеста: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest/clear-all', methods=['DELETE'])
def clear_all_backtests():
    """Удаляет все завершенные бэктесты"""
    try:
        import shutil

        # Получаем список всех task_id из базы
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT task_id FROM backtest_history WHERE status = "completed"')
            task_ids = [row['task_id'] for row in cursor.fetchall()]

            # Удаляем все записи
            cursor.execute('DELETE FROM backtest_history WHERE status = "completed"')
            deleted_count = cursor.rowcount
            conn.commit()

        # Очищаем память
        for task_id in task_ids:
            if task_id in running_backtests:
                del running_backtests[task_id]
            if task_id in backtest_results:
                del backtest_results[task_id]

            # Удаляем директории с отчетами
            report_dir = f"reports/report_{task_id}"
            if os.path.exists(report_dir):
                shutil.rmtree(report_dir)

        print(f"[DELETE] Удалено {deleted_count} бэктестов")

        return jsonify({
            'success': True,
            'message': f'Удалено {deleted_count} бэктестов',
            'deleted_count': deleted_count
        })

    except Exception as e:
        print(f"[DELETE ERROR] Ошибка очистки бэктестов: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/visualization/<task_id>')
def get_visualization(task_id):
    """API для получения plotly визуализации"""
    try:
        # Получаем результаты
        if task_id in backtest_results:
            results = backtest_results[task_id]
        else:
            results = load_backtest_from_db(task_id)
            if not results:
                return jsonify({'error': 'Результаты не найдены'}), 404
            backtest_results[task_id] = results

        # Получаем OHLCV данные если есть
        data = None
        if 'data_summary' in results and results['data_summary']:
            # Пытаемся восстановить данные из конфига
            config = results.get('config', {})
            data_source = config.get('data_source', {})

            if data_source.get('type') == 'csv':
                file_path = data_source.get('file')
                if file_path and os.path.exists(file_path):
                    try:
                        loader = DataLoader()
                        data = loader.load_from_csv(file_path, config.get('symbol'))
                    except Exception as e:
                        print(f"Ошибка загрузки данных для визуализации: {e}")

        # Создаем визуализатор
        viz = BacktestVisualizer(results, data)

        # Получаем тип графика из параметров
        chart_type = request.args.get('type', 'all')

        # Создаем график
        if chart_type == 'all':
            fig = viz.plot_all()
        elif chart_type == 'price':
            fig = viz.plot_price_and_trades()
        elif chart_type == 'balance':
            fig = viz.plot_balance()
        elif chart_type == 'pnl':
            fig = viz.plot_pnl()
        elif chart_type == 'drawdown':
            fig = viz.plot_drawdown()
        elif chart_type == 'distribution':
            fig = viz.plot_trade_distribution()
        else:
            return jsonify({'error': f'Неизвестный тип графика: {chart_type}'}), 400

        # Вместо HTML возвращаем JSON с данными для Plotly
        graph_json = fig.to_json()

        return jsonify({
            'success': True,
            'graph_json': graph_json,
            'task_id': task_id,
            'chart_type': chart_type
        })

    except Exception as e:
        import traceback
        print(f"Ошибка визуализации: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/visualization/<task_id>')
def visualization_page(task_id):
    """Страница с интерактивной визуализацией"""
    # Проверяем существование результатов
    if task_id not in backtest_results:
        results = load_backtest_from_db(task_id)
        if not results:
            flash('Результаты не найдены', 'error')
            return redirect(url_for('results_page'))
        backtest_results[task_id] = results

    return render_template('visualization.html', task_id=task_id)

@app.route('/test-plotly')
def test_plotly():
    """Тестовая страница Plotly"""
    return render_template('test_plotly.html')

@app.route('/health')
def health_check():
    """Health check endpoint for container orchestration"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Страница не найдена'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

if __name__ == '__main__':
    # Создаем необходимые директории
    os.makedirs('data', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Инициализируем базу данных
    init_database()
    
    app.run(host='0.0.0.0', port=8000, debug=True) 