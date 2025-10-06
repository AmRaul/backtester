# CI/CD Setup Guide

## Настройка GitHub Actions для проекта Backtester

Этот проект теперь включает полноценный CI/CD pipeline через GitHub Actions.

## 🚀 Возможности

- ✅ Автоматическое тестирование кода
- ✅ Проверка качества кода (linting)
- ✅ Сборка Docker образов
- ✅ Публикация образов в GitHub Container Registry
- ✅ Сканирование безопасности (Trivy)
- ✅ Поддержка релизов
- 🔄 Опциональный автоматический деплой

## 📋 Требования

1. GitHub репозиторий
2. GitHub Packages включен (бесплатно для публичных репо)

## ⚙️ Настройка

### 1. Включить GitHub Packages

Образы Docker будут публиковаться в GitHub Container Registry (ghcr.io).

1. Перейдите в Settings репозитория
2. Secrets and variables → Actions
3. Убедитесь, что `GITHUB_TOKEN` доступен (он создается автоматически)

### 2. Настроить права доступа

1. Settings → Actions → General
2. Workflow permissions → выберите "Read and write permissions"
3. Сохраните изменения

### 3. (Опционально) Настроить автоматический деплой

Если хотите автоматически деплоить на сервер:

1. Раскомментируйте секцию `deploy` в `.github/workflows/ci-cd.yml`
2. Добавьте secrets в настройках репозитория:
   - `DEPLOY_HOST` - IP или домен вашего сервера
   - `DEPLOY_USER` - SSH пользователь
   - `DEPLOY_KEY` - приватный SSH ключ

```bash
# Создание SSH ключа для деплоя
ssh-keygen -t ed25519 -C "github-actions-deploy" -f deploy_key
# Добавьте deploy_key.pub на сервер в ~/.ssh/authorized_keys
# Добавьте содержимое deploy_key в GitHub Secret DEPLOY_KEY
```

## 📦 Использование

### Автоматическая сборка

Pipeline запускается автоматически при:
- Push в ветки `main` или `develop`
- Создании Pull Request
- Ручном запуске (workflow_dispatch)

### Стадии Pipeline

1. **Test** - Запуск тестов Python
2. **Lint** - Проверка качества кода
3. **Build** - Сборка Docker образов
4. **Security Scan** - Сканирование уязвимостей
5. **Deploy** (опционально) - Деплой на сервер

### Просмотр результатов

1. Перейдите во вкладку "Actions" в вашем репозитории
2. Выберите workflow run для просмотра деталей
3. Проверьте логи каждой стадии

## 🐳 Использование образов

### Локальная разработка

```bash
docker-compose up -d
```

### Production (с образами из registry)

```bash
# Авторизация в GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Запуск с production конфигурацией
export GITHUB_REPOSITORY=username/backtester
docker-compose -f docker-compose.prod.yml up -d
```

### Скачивание конкретной версии

```bash
# Latest версия
docker pull ghcr.io/username/backtester-web:latest

# Конкретная версия
docker pull ghcr.io/username/backtester-web:v1.0.0

# По commit SHA
docker pull ghcr.io/username/backtester-web:main-abc1234
```

## 🏷️ Создание релизов

1. Создайте тег:
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

2. Создайте Release в GitHub:
   - Перейдите в Releases → Create a new release
   - Выберите тег
   - Добавьте описание изменений
   - Опубликуйте

3. Автоматически запустится workflow `release.yml`, который:
   - Соберет образы для multiple платформ (amd64, arm64)
   - Опубликует с тегами версии

## 🔍 Проверка образов

```bash
# Список доступных образов
gh api /user/packages/container/backtester-web/versions

# Запуск конкретного образа
docker run -p 8000:8000 ghcr.io/username/backtester-web:latest
```

## 🛠️ Troubleshooting

### Ошибка "permission denied" при публикации образов

Убедитесь, что в Settings → Actions → General установлено "Read and write permissions"

### Образы не появляются в Packages

1. Проверьте, что workflow успешно завершился
2. Убедитесь, что это не Pull Request (для PR образы не публикуются)
3. Проверьте логи шага "Build and push Docker image"

### Деплой не работает

1. Проверьте SSH подключение вручную
2. Убедитесь, что все secrets правильно настроены
3. Проверьте путь к приложению на сервере

## 📊 Badge статуса

Добавьте в README.md badge статуса CI:

```markdown
![CI/CD Pipeline](https://github.com/username/backtester/actions/workflows/ci-cd.yml/badge.svg)
```

## 🔐 Безопасность

- Образы сканируются на уязвимости через Trivy
- Результаты доступны в GitHub Security
- Не коммитьте секреты в код
- Используйте GitHub Secrets для чувствительных данных

## 📝 Дополнительные настройки

### Кастомизация тестов

Отредактируйте шаг "Run tests" в `.github/workflows/ci-cd.yml`:

```yaml
- name: Run tests
  run: |
    pytest test_indicators.py -v --cov=. --cov-report=xml
    # Добавьте другие тесты здесь
```

### Настройка уведомлений

Добавьте уведомления в Slack/Discord/Email:

```yaml
- name: Notify on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## 🎯 Best Practices

1. Всегда тестируйте локально перед push
2. Используйте осмысленные commit messages
3. Создавайте Pull Requests для важных изменений
4. Регулярно обновляйте зависимости
5. Проверяйте результаты security scan
6. Тегируйте стабильные версии
# 🚀 CI/CD Quick Start

## За 5 минут до работающего CI/CD

### Шаг 1: Загрузите код на GitHub

```bash
# Если репозиторий еще не создан
git init
git add .
git commit -m "Initial commit with CI/CD"
git branch -M main
git remote add origin https://github.com/USERNAME/backtester.git
git push -u origin main
```

### Шаг 2: Настройте права в GitHub

1. Откройте ваш репозиторий на GitHub
2. Перейдите в **Settings** → **Actions** → **General**
3. В секции **Workflow permissions** выберите **Read and write permissions**
4. Нажмите **Save**

### Шаг 3: Готово! 🎉

При следующем push GitHub Actions автоматически:
- ✅ Запустит тесты
- ✅ Проверит качество кода
- ✅ Соберет Docker образы
- ✅ Опубликует их в GitHub Packages

### Просмотр результатов

1. Перейдите во вкладку **Actions** в вашем репозитории
2. Вы увидите запущенные workflows
3. Кликните на любой для просмотра деталей

### Использование образов

После успешной сборки:

```bash
# Авторизация (используйте Personal Access Token с правами read:packages)
echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Запуск последней версии
export GITHUB_REPOSITORY=username/backtester
docker-compose -f docker-compose.prod.yml up -d
```

### Создание Personal Access Token

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token → выберите `read:packages` и `write:packages`
3. Скопируйте токен и используйте для docker login

### Ручной запуск workflow

1. Actions → выберите **CI/CD Pipeline**
2. Нажмите **Run workflow**
3. Выберите ветку и нажмите **Run workflow**

### Что дальше?

- 📖 Полная документация: [CI_CD_SETUP.md](CI_CD_SETUP.md)
- 🔧 Настройка автодеплоя на сервер
- 🏷️ Создание релизов с версионированием
- 🔔 Настройка уведомлений

### Troubleshooting

**Ошибка прав при публикации образов:**
- Проверьте Workflow permissions (шаг 2)

**Образы не появляются в Packages:**
- Убедитесь, что это не Pull Request
- Проверьте логи workflow

**Нужна помощь?**
- Проверьте [CI_CD_SETUP.md](CI_CD_SETUP.md)
- Посмотрите логи в Actions tab
# 🚀 Настройка автоматического деплоя на сервер

## Пошаговая инструкция

### Шаг 1: Подготовка сервера

#### 1.1 Подключитесь к серверу
```bash
ssh user@your-server.com
```

#### 1.2 Установите Docker и Docker Compose
```bash
# Обновите систему
sudo apt update && sudo apt upgrade -y

# Установите Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавьте пользователя в группу docker
sudo usermod -aG docker $USER

# Установите Docker Compose
sudo apt install docker-compose-plugin -y

# Перезайдите в систему для применения изменений
exit
ssh user@your-server.com

# Проверьте установку
docker --version
docker compose version
```

#### 1.3 Создайте директорию для приложения
```bash
sudo mkdir -p /opt/backtester
sudo chown $USER:$USER /opt/backtester
cd /opt/backtester
```

#### 1.4 Создайте необходимые директории
```bash
mkdir -p data reports logs db templates
```

---

### Шаг 2: Создание SSH ключа для GitHub Actions

#### 2.1 На вашем компьютере создайте SSH ключ
```bash
# Создайте новый SSH ключ специально для деплоя
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy_key

# НЕ СТАВЬТЕ ПАРОЛЬ (просто нажмите Enter)
# Это важно для автоматического деплоя
```

Будут созданы два файла:
- `~/.ssh/github_deploy_key` - приватный ключ (для GitHub)
- `~/.ssh/github_deploy_key.pub` - публичный ключ (для сервера)

#### 2.2 Скопируйте публичный ключ на сервер
```bash
# Способ 1: Используйте ssh-copy-id
ssh-copy-id -i ~/.ssh/github_deploy_key.pub user@your-server.com

# Способ 2: Вручную
cat ~/.ssh/github_deploy_key.pub
# Скопируйте вывод, затем на сервере:
# echo "ВСТАВЬТЕ_СКОПИРОВАННЫЙ_КЛЮЧ" >> ~/.ssh/authorized_keys
```

#### 2.3 Проверьте подключение
```bash
ssh -i ~/.ssh/github_deploy_key user@your-server.com
# Должно подключиться БЕЗ запроса пароля
```

---

### Шаг 3: Настройка GitHub Secrets

#### 3.1 Откройте ваш репозиторий на GitHub
```
https://github.com/USERNAME/backtester
```

#### 3.2 Перейдите в Settings → Secrets and variables → Actions

#### 3.3 Добавьте секреты (нажмите "New repository secret")

**Secret 1: DEPLOY_HOST**
- Name: `DEPLOY_HOST`
- Value: `your-server.com` (или IP: `123.45.67.89`)

**Secret 2: DEPLOY_USER**
- Name: `DEPLOY_USER`
- Value: `your-username` (пользователь на сервере)

**Secret 3: DEPLOY_KEY**
- Name: `DEPLOY_KEY`
- Value: Скопируйте содержимое приватного ключа:

```bash
# На вашем компьютере выполните:
cat ~/.ssh/github_deploy_key

# Скопируйте ВСЁ содержимое включая строки:
# -----BEGIN OPENSSH PRIVATE KEY-----
# ...
# -----END OPENSSH PRIVATE KEY-----
```

Вставьте в поле Value как есть, со всеми переносами строк.

**Secret 4: GITHUB_REPOSITORY** (опционально)
- Name: `GITHUB_REPOSITORY`
- Value: `username/backtester` (ваш username и название репо)

---

### Шаг 4: Подготовка файлов на сервере

#### 4.1 Подключитесь к серверу
```bash
ssh user@your-server.com
cd /opt/backtester
```

#### 4.2 Создайте файл docker-compose.prod.yml
```bash
nano docker-compose.prod.yml
```

Вставьте содержимое (замените username/backtester на ваши данные):
```yaml
version: '3.8'

services:
  backtester-web:
    image: ghcr.io/username/backtester-web:latest
    container_name: backtester_web_prod
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./reports:/app/reports
      - ./logs:/app/logs
      - ./db:/app/db
      - ./config.json:/app/config.json:ro
    environment:
      - PYTHONUNBUFFERED=1
      - FLASK_ENV=production
    networks:
      - backtester_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    container_name: backtester_redis_prod
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - backtester_network
    command: redis-server --appendonly yes --requirepass your_strong_password
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

networks:
  backtester_network:
    driver: bridge

volumes:
  redis_data:
    driver: local
```

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

#### 4.3 Создайте базовый config.json
```bash
nano config.json
```

Вставьте минимальную конфигурацию:
```json
{
  "exchange": "binance",
  "symbol": "BTC/USDT",
  "timeframe": "1h",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_balance": 10000
}
```

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

---

### Шаг 5: Первый деплой вручную (тест)

#### 5.1 Авторизуйтесь в GitHub Container Registry

Сначала создайте Personal Access Token на GitHub:
1. GitHub → Settings (справа вверху на вашем аватаре)
2. Developer settings → Personal access tokens → Tokens (classic)
3. Generate new token (classic)
4. Выберите scopes: `read:packages`, `write:packages`
5. Generate token и скопируйте токен

На сервере выполните:
```bash
echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

#### 5.2 Запустите приложение
```bash
cd /opt/backtester
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

#### 5.3 Проверьте что работает
```bash
# Проверьте статус
docker compose -f docker-compose.prod.yml ps

# Проверьте логи
docker compose -f docker-compose.prod.yml logs -f

# Проверьте health check
curl http://localhost:8000/health
```

Должны увидеть:
```json
{"status":"healthy","timestamp":"...","version":"1.0.0"}
```

---

### Шаг 6: Включение автодеплоя в GitHub Actions

#### 6.1 Откройте файл workflow
На вашем компьютере откройте `.github/workflows/ci-cd.yml`

#### 6.2 Раскомментируйте секцию deploy
Найдите эти строки (в конце файла):
```yaml
  # deploy:
  #   name: Deploy to Server
  #   runs-on: ubuntu-latest
  #   needs: [build, security-scan]
  #   if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  #
  #   steps:
  #     - name: Deploy to production
  #       uses: appleboy/ssh-action@v1.0.0
  #       with:
  #         host: ${{ secrets.DEPLOY_HOST }}
  #         username: ${{ secrets.DEPLOY_USER }}
  #         key: ${{ secrets.DEPLOY_KEY }}
  #         script: |
  #           cd /path/to/app
  #           docker-compose pull
  #           docker-compose up -d
  #           docker system prune -f
```

Уберите все `#` и замените `/path/to/app`:
```yaml
  deploy:
    name: Deploy to Server
    runs-on: ubuntu-latest
    needs: [build, security-scan]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'

    steps:
      - name: Deploy to production
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_KEY }}
          script: |
            cd /opt/backtester
            echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin
            docker compose -f docker-compose.prod.yml pull
            docker compose -f docker-compose.prod.yml up -d
            docker system prune -f
            echo "Deployment completed!"
```

---

### Шаг 7: Тестирование автодеплоя

#### 7.1 Закоммитьте изменения
```bash
git add .github/workflows/ci-cd.yml
git commit -m "Enable automatic deployment"
git push origin main
```

#### 7.2 Следите за процессом
1. Откройте GitHub → ваш репозиторий → вкладка **Actions**
2. Вы увидите новый workflow run
3. Дождитесь прохождения всех стадий:
   - ✅ Test
   - ✅ Lint
   - ✅ Build
   - ✅ Security Scan
   - ✅ Deploy

#### 7.3 Проверьте на сервере
```bash
ssh user@your-server.com
cd /opt/backtester
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=50
```

---

### Шаг 8: Настройка Nginx (опционально, но рекомендуется)

#### 8.1 Установите Nginx на сервере
```bash
sudo apt install nginx -y
```

#### 8.2 Создайте конфигурацию
```bash
sudo nano /etc/nginx/sites-available/backtester
```

Вставьте:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Замените на ваш домен или IP

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 8.3 Активируйте конфигурацию
```bash
sudo ln -s /etc/nginx/sites-available/backtester /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 8.4 (Опционально) Настройте HTTPS с Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

## ✅ Готово! Как это работает теперь:

1. **Вы делаете изменения в коде** → `git push origin main`
2. **GitHub Actions автоматически**:
   - ✅ Запускает тесты
   - ✅ Проверяет качество кода
   - ✅ Собирает Docker образы
   - ✅ Публикует в ghcr.io
   - ✅ Сканирует на уязвимости
   - ✅ **Автоматически деплоит на ваш сервер!**
3. **Через 5-10 минут** новая версия уже работает на сервере

---

## 🔧 Troubleshooting

### Ошибка "Permission denied" при SSH
```bash
# Проверьте права на приватный ключ
chmod 600 ~/.ssh/github_deploy_key

# Проверьте подключение
ssh -i ~/.ssh/github_deploy_key -v user@your-server.com
```

### Ошибка при docker login на сервере
```bash
# Убедитесь что токен имеет права read:packages
# Пересоздайте токен на GitHub с правильными правами
```

### Деплой не запускается
- Убедитесь что push в ветку `main` (не `develop`)
- Проверьте что все secrets добавлены в GitHub
- Посмотрите логи workflow в Actions

### Приложение не запускается после деплоя
```bash
# На сервере проверьте логи
cd /opt/backtester
docker compose -f docker-compose.prod.yml logs -f backtester-web
```

---

## 📊 Мониторинг

### Проверка статуса
```bash
# Health check
curl http://your-server.com/health

# Docker статус
docker compose -f docker-compose.prod.yml ps

# Логи последние 100 строк
docker compose -f docker-compose.prod.yml logs --tail=100
```

### Ручной откат к предыдущей версии
```bash
cd /opt/backtester

# Используйте конкретный тег
docker compose -f docker-compose.prod.yml down
# Измените в docker-compose.prod.yml: image: ghcr.io/user/backtester-web:v1.0.0
docker compose -f docker-compose.prod.yml up -d
```

---

## 🎯 Что делать дальше?

- ✅ Настроить мониторинг (Prometheus + Grafana)
- ✅ Добавить уведомления в Slack/Discord при деплое
- ✅ Настроить backup базы данных
- ✅ Настроить логирование (ELK stack)

**Поздравляю! У вас теперь полноценный CI/CD! 🚀**
