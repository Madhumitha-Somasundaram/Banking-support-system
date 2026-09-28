FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY services ./services
COPY shared ./shared

EXPOSE 8102

CMD ["uvicorn", "services.transaction.main:app", "--host", "0.0.0.0", "--port", "8102"]