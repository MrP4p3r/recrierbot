FROM alpine:3.7

COPY ./dist-alpine/main /main
COPY ./start.sh /start.sh


CMD ["sh", "start.sh"]
