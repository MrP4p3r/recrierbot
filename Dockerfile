FROM mrp4p3r/pyinstaller-alpine-py3

COPY ./. /src
RUN /pyinstaller/pyinstaller.sh --noconfirm --log-level DEBUG --distpath /src/dist-alpine -F main.py && \
    chmod +x /src/dist-alpine/main /src/start.sh

FROM alpine:3.7

COPY --from=0 /src/dist-alpine/main /main
COPY --from=0 /src/start.sh /start.sh

CMD ["sh", "/start.sh"]
