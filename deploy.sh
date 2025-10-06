#!/bin/bash

# Скрипт для деплоя backtester приложения
# Используется GitHub Actions или может быть запущен вручную

set -e  # Остановиться при любой ошибке

echo "🚀 Starting deployment..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка переменных окружения
if [ -z "$GITHUB_REPOSITORY" ]; then
    echo -e "${RED}Error: GITHUB_REPOSITORY environment variable is not set${NC}"
    exit 1
fi

# Загрузка .env файла если существует
if [ -f .env ]; then
    echo -e "${GREEN}Loading environment variables from .env${NC}"
    export $(cat .env | grep -v '^#' | xargs)
fi

echo -e "${YELLOW}Pulling latest Docker images...${NC}"
docker-compose -f docker-compose.prod.yml pull

echo -e "${YELLOW}Stopping old containers...${NC}"
docker-compose -f docker-compose.prod.yml down

echo -e "${YELLOW}Starting new containers...${NC}"
docker-compose -f docker-compose.prod.yml up -d

echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Проверка health check
if curl -f http://localhost:${WEB_PORT:-8000}/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Application is healthy!${NC}"
else
    echo -e "${RED}❌ Health check failed!${NC}"
    echo "Container logs:"
    docker-compose -f docker-compose.prod.yml logs --tail=50
    exit 1
fi

echo -e "${YELLOW}Cleaning up old images...${NC}"
docker system prune -f

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "Application is running at: http://localhost:${WEB_PORT:-8000}"
echo "Check status: docker-compose -f docker-compose.prod.yml ps"
echo "View logs: docker-compose -f docker-compose.prod.yml logs -f"
