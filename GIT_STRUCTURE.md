# 📁 Структура проекта и Git

## ✅ Что ДОЛЖНО быть в Git

### Исходный код
```
backtester.py       - Основной движок бэктестера
strategy.py         - Торговые стратегии
data_loader.py      - Загрузка данных
indicators.py       - Технические индикаторы
reporter.py         - Генерация отчетов
main.py            - CLI интерфейс
web_app.py         - Веб интерфейс
test_indicators.py - Тесты
```

### Конфигурация
```
requirements.txt          - Python зависимости
.env.example             - Пример переменных окружения
config_examples.json     - Примеры конфигураций
config_api_examples.json - Примеры API конфигов
.gitignore              - Что игнорировать
.dockerignore           - Что игнорировать в Docker
```

### Docker и CI/CD
```
Dockerfile                  - Основной образ
Dockerfile.web             - Образ для web приложения
docker-compose.yml         - Dev окружение
docker-compose.prod.yml    - Production окружение
deploy.sh                  - Скрипт деплоя
.github/workflows/         - GitHub Actions
```

### Шаблоны
```
templates/                 - HTML шаблоны для web интерфейса
  ├── base.html
  ├── index.html
  ├── config.html
  ├── results.html
  └── report.html
```

### Документация
```
README.md               - Главная документация
CI_CD_FULL_GUIDE.md    - Гайд по CI/CD
CONFIG_DESCRIPTION.md  - Описание конфигураций
PROJECT_SUMMARY.md     - Обзор проекта
```

### Пустые папки (с .gitkeep)
```
data/     - Исторические данные (только .gitkeep)
db/       - База данных (только .gitkeep)
reports/  - Отчеты (только .gitkeep)
logs/     - Логи (только .gitkeep)
```

---

## ❌ Что НЕ должно быть в Git

### Генерируемые данные
```
db/backtester.db       - База данных SQLite
data/*.csv             - Скачанные исторические данные
reports/*              - Сгенерированные отчеты (PNG, CSV, JSON)
logs/*.log             - Файлы логов
results/               - Результаты бэктестов
```

### Приватная конфигурация
```
.env                   - Переменные окружения
config.json           - Рабочая конфигурация (может содержать API ключи)
```

### IDE и система
```
.idea/                - PyCharm/IntelliJ настройки
.vscode/              - VSCode настройки
.DS_Store             - macOS системные файлы
.claude/              - Claude Code настройки
__pycache__/          - Python кэш
*.pyc                 - Скомпилированные Python файлы
```

### Временные файлы
```
debug_calculations.py - Файлы для дебага
*.log                 - Логи
.pytest_cache/        - Кэш тестов
coverage.xml          - Отчеты о покрытии
```

---

## 🐳 Что попадает в Docker образ

Docker образ собирается из **исходников в Git**, НО:

### Включается:
- Весь исходный код (*.py)
- requirements.txt
- templates/
- Конфиги (config_examples.json)

### Исключается (.dockerignore):
- .git/
- .github/
- .idea/
- .vscode/
- __pycache__/
- *.pyc
- .venv/
- tests/
- *.md (документация)
- data/
- reports/
- logs/
- db/

---

## 🚀 Что попадает на сервер при деплое

### При деплое GitHub Actions:
1. Собирает Docker образ из Git
2. Пушит образ в `ghcr.io/amraul/backtester-web:latest`
3. На сервере запускает `docker pull` (скачивает образ)
4. Запускает контейнер

### На сервере существует отдельно:
```
/opt/backtester/
├── docker-compose.prod.yml  - Конфиг запуска
├── config.json              - Production конфигурация
├── data/                    - Данные (volume)
├── db/                      - База данных (volume)
├── reports/                 - Отчеты (volume)
└── logs/                    - Логи (volume)
```

**Важно:** Volumes (data/, db/, reports/, logs/) живут на сервере и НЕ перезаписываются при деплое!

---

## 📋 Итоговый размер

### Git репозиторий (~500KB):
- Только исходники и конфиги
- Без данных, отчетов, БД
- Легко клонировать и работать

### Docker образ (~500MB):
- Python + библиотеки
- Исходный код приложения
- Без данных (они в volumes)

### На сервере (растет со временем):
- Docker образ: ~500MB
- Volumes (data/db/reports): зависит от использования

---

## 🔄 Workflow при разработке

1. **Локально меняете код** → `git push`
2. **GitHub Actions:**
   - Запускает тесты
   - Собирает новый Docker образ
   - Пушит в registry
   - Деплоит на сервер
3. **На сервере:**
   - Скачивает новый образ
   - Перезапускает контейнер
   - **Данные остаются!** (db/, reports/, data/)

---

## ✨ Преимущества такой структуры

1. **Чистый Git** - только код и конфиги
2. **Быстрый клон** - нет мусорных файлов
3. **Безопасность** - нет приватных данных в Git
4. **Переносимость** - клонируй и запускай где угодно
5. **Автоматизация** - CI/CD работает из коробки
