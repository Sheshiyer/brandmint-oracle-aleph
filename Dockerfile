FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml requirements.txt ./
COPY brandmint ./brandmint

RUN pip install --no-cache-dir .

ENTRYPOINT ["bm"]
CMD ["--help"]
