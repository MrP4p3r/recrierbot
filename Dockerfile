FROM alpine:3.7

COPY ./dist-alpine/main /main
COPY ./start.sh /start.sh

RUN chmod +x /start.sh /main

CMD ["start.sh"]
