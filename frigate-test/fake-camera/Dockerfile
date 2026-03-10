FROM python:3.11-slim

RUN pip install Pillow --no-cache-dir

WORKDIR /app
COPY camera_server.py .

RUN mkdir -p /images

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

CMD ["python3", "camera_server.py"]
