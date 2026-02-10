FROM python:3.12-alpine

RUN apk add --no-cache \
    build-base \
    postgresql-dev

RUN mkdir -p /app

WORKDIR /app

ENV PYTHONPATH=/app

RUN pip install --upgrade pip

COPY core_requirements.txt .
RUN pip install --no-cache-dir -r core_requirements.txt

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./app

EXPOSE 8000

CMD ["python", "app/main.py"]