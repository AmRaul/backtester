# 🐳 Решение проблем с Docker

## Проблема с сетью при сборке

Если при сборке Docker образа возникает ошибка:
```
Temporary failure resolving 'deb.debian.org'
```

### Решение 1: Использование минимальной версии

Запустите минимальную версию без системных пакетов:

```bash
# Сборка минимальной версии
./docker-run.sh build --minimal

# Запуск веб-интерфейса
./docker-run.sh web --minimal
```

### Решение 2: Настройка DNS для Docker

#### macOS:
```bash
# Перезапуск Docker Desktop
# Docker Desktop -> Preferences -> Reset -> Restart Docker

# Или через терминал
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

#### Linux:
```bash
# Настройка DNS для Docker
sudo systemctl restart docker

# Или добавить DNS в daemon.json
sudo tee /etc/docker/daemon.json <<EOF
{
  "dns": ["8.8.8.8", "8.8.4.4"]
}
EOF

sudo systemctl restart docker
```

### Решение 3: Использование другого базового образа

Если проблемы продолжаются, можно использовать Alpine Linux:

```dockerfile
FROM python:3.11-alpine

# Установка зависимостей для Alpine
RUN apk add --no-cache gcc musl-dev
```

### Решение 4: Сборка без кэша

```bash
# Очистка всех образов и пересборка
./docker-run.sh clean
./docker-run.sh build --minimal
```

## Другие частые проблемы

### Порт уже занят

```bash
# Проверить какой процесс использует порт 8000
lsof -i :8000

# Остановить все контейнеры
./docker-run.sh stop

# Или принудительно убить процесс
sudo kill -9 <PID>
```

### Проблемы с правами доступа

```bash
# Изменить владельца директорий
sudo chown -R $USER:$USER data reports logs

# Или запустить с правами root
docker-compose run --user root backtester-web
```

### Недостаточно места на диске

```bash
# Очистка неиспользуемых образов
docker system prune -a

# Очистка volumes
docker volume prune

# Полная очистка
./docker-run.sh clean
```

### Проблемы с зависимостями Python

Если возникают ошибки установки Python пакетов:

```bash
# Обновление pip в контейнере
docker-compose exec backtester-web pip install --upgrade pip

# Переустановка зависимостей
docker-compose exec backtester-web pip install -r requirements.txt --force-reinstall
```

## Логи и диагностика

### Просмотр логов

```bash
# Все логи
./docker-run.sh logs

# Логи конкретного сервиса
./docker-run.sh logs backtester-web

# Логи в реальном времени
docker-compose logs -f backtester-web
```

### Подключение к контейнеру

```bash
# Подключиться к работающему контейнеру
docker-compose exec backtester-web bash

# Или запустить новый контейнер для отладки
docker-compose run --rm backtester-web bash
```

### Проверка состояния

```bash
# Статус контейнеров
docker-compose ps

# Использование ресурсов
docker stats

# Информация об образах
docker images
```

## Альтернативные способы запуска

### Без Docker Compose

```bash
# Сборка образа
docker build -t backtester .

# Запуск CLI
docker run --rm -v $(pwd)/data:/app/data backtester python main.py --help

# Запуск веб-интерфейса
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data backtester python web_app.py
```

### Локальный запуск (без Docker)

Если Docker не работает, можно запустить локально:

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск CLI
python main.py --help

# Запуск веб-интерфейса
python web_app.py
```

## Контакты для поддержки

Если проблемы не решаются:

1. Проверьте логи: `./docker-run.sh logs`
2. Попробуйте минимальную версию: `./docker-run.sh web --minimal`
3. Используйте локальный запуск: `python main.py --help`
4. Создайте issue с описанием проблемы и логами 