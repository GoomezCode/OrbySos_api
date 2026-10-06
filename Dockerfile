FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requeriments.txt .

RUN pip install --no-cache-dir -r requeriments.txt

COPY main.py .
COPY core ./core
COPY routers ./routers
COPY services ./services
COPY repositories ./repositories
COPY schemas ./schemas
COPY middleware ./middleware
COPY api ./api
COPY classes ./classes
COPY database ./database
COPY util ./util

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]