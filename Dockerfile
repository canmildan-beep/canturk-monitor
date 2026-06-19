FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Varsayilan komut (docker-compose her servis icin ayri komut verir)
CMD ["python", "-m", "app.listener"]
