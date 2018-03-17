#!/bin/sh

set -e

if [ "$TELEGRAM_TOKEN" == "" ]; then
    echo TELEGRAM_TOKEN is not provided.
    exit 1
fi

if [ "BOT_URL" == "" ]; then
    echo BOT_URL is not provided.
    echo Example: \'https://example.com\'
    exit 1
fi

export DB_PATH=${DB_PATH:-/var/lib/recrierbot/db.sqlite3}
export CHAT_TOKENS_LIMIT=${CHAT_TOKENS_LIMIT:-7}
export THREADS_NUMBER=${THREADS_NUMBER:-4}
export TORNADO_PORT=${TORNADO_PORT:-8080}


mkdir -p $(dirname $DB_PATH)


/main
