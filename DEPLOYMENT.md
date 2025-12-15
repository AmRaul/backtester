# Инструкция по развертыванию с Nginx

## Настройка поддомена

### 1. Добавить DNS запись ✅

В настройках вашего домена `hub-cargo.ru` добавьте A-запись:

```
Тип: A
Имя: backtester
Значение: 5.35.80.213
TTL: 3600
```

После добавления подождите 5-30 минут для распространения DNS.

Проверить можно командой:
```bash
ping backtester.hub-cargo.ru
```

### 2. Проверить GitHub Secrets ✅

Убедитесь, что в GitHub Actions → Secrets добавлены следующие переменные:

- ✅ `DOMAIN` = `backtester.hub-cargo.ru`
- ✅ `LETSENCRYPT_EMAIL` = ваш email
- ✅ `WEB_PORT` = `8000`
- ✅ `REDIS_PASSWORD` = надёжный пароль
- ✅ `HOST` = IP сервера
- ✅ `USER` = пользователь сервера
- ✅ `SSH_KEY` = SSH ключ для доступа

### 3. Деплой

Просто сделайте push в main ветку:

```bash
git add .
git commit -m "Add Nginx reverse proxy configuration"
git push origin main
```

GitHub Actions автоматически:
1. Соберёт Docker образы
2. Создаст `.env` файл на сервере из Secrets
3. Запустит backtester приложение
4. Установит Nginx конфигурацию (если ещё не установлена)
5. Получит SSL сертификат от Let's Encrypt через Certbot
6. Перезагрузит Nginx

### 4. Проверка

После успешного деплоя ваше приложение будет доступно по адресу:

🌐 **https://backtester.hub-cargo.ru**

HTTP автоматически редиректится на HTTPS.

## Ручное развертывание на сервере (опционально)

Если нужно развернуть вручную:

```bash
# 1. Подключитесь к серверу
ssh user@5.35.80.213

# 2. Перейдите в директорию проекта
cd /opt/backtester

# 3. Создайте .env файл
cp .env.example .env
nano .env  # Заполните реальные значения

# 4. Запустите приложение
docker compose -f docker-compose.prod.yml up -d

# 5. Установите Nginx конфигурацию
sudo cp nginx/backtester.conf /etc/nginx/sites-available/backtester.conf
sudo ln -s /etc/nginx/sites-available/backtester.conf /etc/nginx/sites-enabled/

# 6. Проверьте конфигурацию Nginx
sudo nginx -t

# 7. Получите SSL сертификат
sudo certbot --nginx -d backtester.hub-cargo.ru --non-interactive --agree-tos -m your-email@example.com

# 8. Перезагрузите Nginx
sudo systemctl reload nginx

# 9. Проверьте логи
docker compose -f docker-compose.prod.yml logs -f
sudo tail -f /var/log/nginx/backtester.access.log
```

## Управление

### Проверка статуса

```bash
# Docker контейнеры
docker compose -f docker-compose.prod.yml ps

# Nginx
sudo systemctl status nginx
```

### Просмотр логов

```bash
# Backtester приложение
docker compose -f docker-compose.prod.yml logs -f backtester-web

# Nginx access log
sudo tail -f /var/log/nginx/backtester.access.log

# Nginx error log
sudo tail -f /var/log/nginx/backtester.error.log
```

### Перезапуск

```bash
# Backtester
docker compose -f docker-compose.prod.yml restart

# Nginx
sudo systemctl reload nginx
```

### Остановка

```bash
docker compose -f docker-compose.prod.yml down
```

## SSL сертификат

- Certbot автоматически получает SSL сертификат от Let's Encrypt
- Сертификат хранится в `/etc/letsencrypt/live/backtester.hub-cargo.ru/`
- Автоматически обновляется каждые 90 дней (через cron job certbot)
- Первое получение сертификата занимает ~30 секунд

### Обновление сертификата вручную

```bash
sudo certbot renew
sudo systemctl reload nginx
```

## Архитектура

```
Интернет (порты 80, 443)
         ↓
    Nginx (reverse proxy)
         ↓
backtester.hub-cargo.ru → Flask App (Docker контейнер, порт 8000)
                           ↓
                         Redis (Docker контейнер, порт 6379)
```

## Безопасность

✅ Только порты 80 и 443 открыты наружу на Nginx
✅ Backtester (8000) доступен только локально через Nginx proxy
✅ Redis (6379) доступен только внутри Docker сети
✅ Автоматический HTTPS с Let's Encrypt
✅ HTTP → HTTPS редирект
✅ Security headers (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection)

## Troubleshooting

### Сертификат не получен

Проверьте логи Certbot:
```bash
sudo certbot certificates
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

Убедитесь, что:
- DNS запись корректна и распространилась (`ping backtester.hub-cargo.ru`)
- Порты 80 и 443 открыты и не заблокированы файрволом
- Email в LETSENCRYPT_EMAIL корректный
- Nginx конфигурация корректна (`sudo nginx -t`)

### Приложение недоступно

1. Проверьте статус контейнеров:
```bash
docker ps
docker compose -f docker-compose.prod.yml ps
```

2. Проверьте статус Nginx:
```bash
sudo systemctl status nginx
sudo nginx -t
```

3. Проверьте логи приложения:
```bash
docker compose -f docker-compose.prod.yml logs backtester-web
```

4. Проверьте логи Nginx:
```bash
sudo tail -f /var/log/nginx/backtester.error.log
```

5. Проверьте, что backtester слушает порт 8000:
```bash
curl http://localhost:8000
```

### 502 Bad Gateway

Это означает, что Nginx не может подключиться к Docker контейнеру:

1. Проверьте, что контейнер запущен:
```bash
docker ps | grep backtester
```

2. Проверьте, что приложение слушает порт 8000:
```bash
docker exec backtester_web_prod curl http://localhost:8000/health
```

3. Если используете Docker на отдельной сети, обновите `upstream` в nginx конфиге на IP контейнера:
```bash
docker inspect backtester_web_prod | grep IPAddress
```

### Редирект на hub-cargo.ru

Если backtester.hub-cargo.ru редиректит на hub-cargo.ru, проверьте:

1. Nginx конфигурация установлена:
```bash
ls -la /etc/nginx/sites-enabled/backtester.conf
```

2. Нет конфликтов с другими конфигурациями:
```bash
sudo nginx -t
grep -r "backtester" /etc/nginx/sites-enabled/
```
