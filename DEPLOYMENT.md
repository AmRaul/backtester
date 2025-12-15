# Инструкция по развертыванию с Traefik

## Настройка поддомена

### 1. Добавить DNS запись

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

### 2. Проверить GitHub Secrets

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
git commit -m "Add Traefik reverse proxy configuration"
git push origin main
```

GitHub Actions автоматически:
1. Соберёт Docker образы
2. Создаст `.env` файл на сервере из Secrets
3. Запустит Traefik
4. Запустит backtester приложение
5. Получит SSL сертификат от Let's Encrypt

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

# 4. Создайте директорию для SSL сертификатов
mkdir -p traefik/letsencrypt
touch traefik/letsencrypt/acme.json
chmod 600 traefik/letsencrypt/acme.json

# 5. Запустите Traefik
docker compose -f docker-compose.traefik.yml up -d

# 6. Запустите приложение
docker compose -f docker-compose.prod.yml up -d

# 7. Проверьте логи
docker compose -f docker-compose.traefik.yml logs -f
docker compose -f docker-compose.prod.yml logs -f
```

## Управление

### Проверка статуса

```bash
docker compose -f docker-compose.traefik.yml ps
docker compose -f docker-compose.prod.yml ps
```

### Просмотр логов

```bash
# Traefik
docker compose -f docker-compose.traefik.yml logs -f traefik

# Backtester
docker compose -f docker-compose.prod.yml logs -f backtester-web
```

### Перезапуск

```bash
docker compose -f docker-compose.prod.yml restart
```

### Остановка

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.traefik.yml down
```

## SSL сертификат

- Traefik автоматически получает SSL сертификат от Let's Encrypt
- Сертификат хранится в `traefik/letsencrypt/acme.json`
- Автоматически обновляется каждые 90 дней
- Первое получение сертификата занимает ~30 секунд

## Архитектура

```
Интернет (порты 80, 443)
         ↓
    Traefik (reverse proxy)
         ↓
backtester.hub-cargo.ru → Flask App (порт 8000, внутренний)
                           ↓
                         Redis (порт 6379, внутренний)
```

## Безопасность

✅ Только порты 80 и 443 открыты наружу
✅ Backtester (8000) доступен только через Traefik
✅ Redis (6379) доступен только внутри Docker сети
✅ Автоматический HTTPS с Let's Encrypt
✅ HTTP → HTTPS редирект

## Troubleshooting

### Сертификат не получен

Проверьте логи Traefik:
```bash
docker compose -f docker-compose.traefik.yml logs traefik
```

Убедитесь, что:
- DNS запись корректна и распространилась
- Порты 80 и 443 открыты на сервере
- Email в LETSENCRYPT_EMAIL корректный

### Приложение недоступно

1. Проверьте статус контейнеров:
```bash
docker ps
```

2. Проверьте логи:
```bash
docker compose -f docker-compose.prod.yml logs backtester-web
```

3. Убедитесь, что Traefik network создан:
```bash
docker network ls | grep traefik
```
