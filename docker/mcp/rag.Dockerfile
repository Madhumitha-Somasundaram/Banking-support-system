FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY mcp-servers ./mcp-servers
COPY shared ./shared

ENV PYTHONPATH=/app

EXPOSE 8004

CMD ["python", "mcp-servers/rag/server.py"]