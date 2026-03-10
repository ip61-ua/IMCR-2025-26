FROM eclipse-mosquitto:2

RUN mosquitto_passwd -b -c /mosquitto/config/passwords frigate      frigate123   && \
    mosquitto_passwd -b    /mosquitto/config/passwords doubletake   doubletake123 && \
    mosquitto_passwd -b    /mosquitto/config/passwords homeassistant homeassistant123 && \
    mosquitto_passwd -b    /mosquitto/config/passwords admin        admin123 && \
    chown mosquitto:mosquitto /mosquitto/config/passwords && \
    chmod 600 /mosquitto/config/passwords

COPY --chown=mosquitto:mosquitto mosquitto.conf /mosquitto/config/mosquitto.conf

EXPOSE 1883