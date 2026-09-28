FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY shared ./shared

ENV PYTHONPATH=/app

EXPOSE 8202

CMD ["uvicorn", "app.agents.card.main:app", "--host", "0.0.0.0", "--port", "8203"]