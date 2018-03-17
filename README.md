# RecrierBot

Бот для оповещений с помощью Telegram

Концептуально основан на https://github.com/hellsman/crierbot


# Команды

- `/start` - Ничего особенного. Просто начинается диалог с ботом.
- `/newtoken` - Создает новый токен для чата.
- `/deltokens` - Удаляет один или несколько указанных через пробел токенов для чата.
- `/listtokens` - Выводит список токенов для чата.
- `/ping` - Pong :wink:


# Docker

Создаем своего Telegram бота через [@BotFather](https://telegram.me/BotFather).
Получаем у него токен.

Пример docker-compose.yml.

```
version: "3.5"

services:
  recrier:
    container_name: recrierbot-container
    image: mrp4p3r/recrierbot
    volumes:
      - recrier-test-db:/var/lib/recrierbot
    environment:
      TELEGRAM_TOKEN: 123456789:ABCDEFGHiGKlMNOprStUVw-xyZOWdysnIKABC
      BOT_URL: http://recrier.example.com/
      CHAT_TOKENS_LIMIT: 7
      LOGGING_LEVEL: INFO
      THREADS_NUMBER: 4
      TORNADO_PORT: 8080
      DB_PATH: /var/lib/recrierbot/db.sqlite3

volumes:
  recrier-test-db:
```

Поднимаем это дело через `docker-compose pull && docker-compose up -d` и используем бота.

TELEGRAM_TOKEN и BOT_URL являются обязательными параметрами.
Остальные параметры опциональны. В примере выше указаны параметры по умолчанию.
Описание параметров

- `TELEGRAM_TOKEN` - Указывается в формате `123456789:ABCDEFGHiGKlMNOprStUVw-xyZOWdysnIKABC`
- `BOT_URL` - Это базовый URL веб-хука для бота. Должен иметь протокол и доменное имя: https://mybot.example.com/
- `CHAT_TOKENS_LIMIT` - Максимальное количество токенов для чата
- `LOGGING_LEVEL` - Уровень логгирования (DEBUG, INFO, WARNING, ERROR или числом; Google: "python logging")
- `THREADS_NUMBER` - Количество потоков для обработки запросов. Четырех должно быть больше чем достаточно.
- `TORNADO_PORT` - Порт, на котором поднят веб-сервер внутри контейнера.
- `DB_PATH` - Путь к файлу базы данных внутри контейнера. Неплохо будет подключить директорию с базой к тому,
              чтобы база не пропадала, если удалить контейнер.


Ссылка, чтобы проверить статус бота (через веб-браузер): `BOT_URL/status`
