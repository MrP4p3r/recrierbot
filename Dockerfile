FROM docker:18
COPY ./. /src
RUN docker run --name botserver-builder -v /src:/src
        mrp4p3r/pyinstaller-alpine-py3 \
            --noconfirm --log-level DEBUG --distpath /src/dist-alpine -F main.py
            mkdir -p ~/repo/dist-alpine
            docker cp botserver-builder:/src/dist-alpine/main ~/src/dist-alpine && \
    chmod +x /src/dist-alpine/main /src/start.sh

FROM alpine:3.7

COPY --from=0 /src/dist-alpine/main /main
COPY --from=0 /src/start.sh /start.sh

CMD ["sh", "/start.sh"]
