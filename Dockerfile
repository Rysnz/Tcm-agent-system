FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HF_ENDPOINT=https://hf-mirror.com

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

COPY . .

RUN mkdir -p /app/media /app/staticfiles /app/apps/logs

EXPOSE 8000

CMD ["gunicorn", "apps.tcm.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
