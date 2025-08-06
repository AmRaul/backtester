#!/bin/bash

# Скрипт для запуска Crypto Backtester в Docker

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода логов
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    error "Docker не установлен!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose не установлен!"
    exit 1
fi

# Создаем необходимые директории
log "Создание директорий..."
mkdir -p data reports logs

# Функция показа помощи
show_help() {
    echo -e "${BLUE}Crypto Backtester - Docker Runner${NC}"
    echo ""
    echo "Использование: $0 [КОМАНДА] [ОПЦИИ]"
    echo ""
    echo "Команды:"
    echo "  web           Запустить веб-интерфейс (по умолчанию)"
    echo "  cli           Запустить CLI версию"
    echo "  build         Собрать Docker образы"
    echo "  stop          Остановить все контейнеры"
    echo "  logs          Показать логи"
    echo "  clean         Очистить все контейнеры и образы"
    echo "  help          Показать эту справку"
    echo ""
    echo "Опции:"
    echo "  --minimal     Использовать минимальную конфигурацию (без системных пакетов)"
    echo ""
    echo "Примеры:"
    echo "  $0 web                    # Запустить веб-интерфейс на http://localhost:8000"
    echo "  $0 web --minimal          # Запустить с минимальной конфигурацией"
    echo "  $0 cli --help             # Показать помощь CLI"
    echo "  $0 cli --list-exchanges   # Показать доступные биржи"
    echo "  $0 build --minimal        # Собрать минимальные образы"
    echo ""
}

# Функция запуска веб-интерфейса
start_web() {
    local use_minimal=false
    
    # Проверяем флаг --minimal
    for arg in "$@"; do
        if [ "$arg" = "--minimal" ]; then
            use_minimal=true
            break
        fi
    done
    
    if [ "$use_minimal" = true ]; then
        log "Запуск веб-интерфейса (минимальная версия)..."
        compose_file="docker-compose.minimal.yml"
        container_name="backtester_web_minimal"
    else
        log "Запуск веб-интерфейса..."
        compose_file="docker-compose.yml"
        container_name="backtester_web"
    fi
    
    # Проверяем, не запущен ли уже
    if docker-compose -f "$compose_file" ps | grep -q "${container_name}.*Up"; then
        warn "Веб-интерфейс уже запущен!"
        log "Доступен по адресу: http://localhost:8000"
        return 0
    fi
    
    # Запускаем веб-сервисы
    if [ "$use_minimal" = true ]; then
        docker-compose -f "$compose_file" up -d backtester-web
    else
        docker-compose -f "$compose_file" up -d backtester-web redis
    fi
    
    # Ждем запуска
    log "Ожидание запуска сервисов..."
    sleep 5
    
    if docker-compose -f "$compose_file" ps | grep -q "${container_name}.*Up"; then
        log "✅ Веб-интерфейс запущен успешно!"
        log "🌐 Доступен по адресу: http://localhost:8000"
        log ""
        log "Для остановки выполните: $0 stop"
        log "Для просмотра логов: $0 logs"
    else
        error "❌ Не удалось запустить веб-интерфейс"
        docker-compose -f "$compose_file" logs backtester-web
        exit 1
    fi
}

# Функция запуска CLI
start_cli() {
    shift # Убираем 'cli' из аргументов
    
    log "Запуск CLI версии..."
    
    if [ $# -eq 0 ]; then
        # Без аргументов - показываем help
        docker-compose run --rm backtester python main.py --help
    else
        # Передаем все аргументы
        docker-compose run --rm backtester python main.py "$@"
    fi
}

# Функция сборки образов
build_images() {
    local use_minimal=false
    
    # Проверяем флаг --minimal
    for arg in "$@"; do
        if [ "$arg" = "--minimal" ]; then
            use_minimal=true
            break
        fi
    done
    
    if [ "$use_minimal" = true ]; then
        log "Сборка минимальных Docker образов..."
        docker-compose -f docker-compose.minimal.yml build --no-cache
    else
        log "Сборка Docker образов..."
        docker-compose build --no-cache
    fi
    
    log "✅ Образы собраны успешно!"
}

# Функция остановки
stop_services() {
    log "Остановка всех сервисов..."
    docker-compose down
    log "✅ Все сервисы остановлены"
}

# Функция показа логов
show_logs() {
    if [ $# -gt 1 ]; then
        # Показать логи конкретного сервиса
        docker-compose logs -f "$2"
    else
        # Показать все логи
        docker-compose logs -f
    fi
}

# Функция очистки
clean_all() {
    warn "Это удалит все контейнеры и образы проекта!"
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Остановка и удаление контейнеров..."
        docker-compose down -v --remove-orphans
        
        log "Удаление образов..."
        docker-compose down --rmi all
        
        log "Очистка неиспользуемых ресурсов..."
        docker system prune -f
        
        log "✅ Очистка завершена"
    else
        log "Отменено"
    fi
}

# Основная логика
case "${1:-web}" in
    "web")
        start_web "$@"
        ;;
    "cli")
        start_cli "$@"
        ;;
    "build")
        build_images "$@"
        ;;
    "stop")
        stop_services
        ;;
    "logs")
        show_logs "$@"
        ;;
    "clean")
        clean_all
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        error "Неизвестная команда: $1"
        show_help
        exit 1
        ;;
esac 