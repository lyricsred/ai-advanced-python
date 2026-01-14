FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "bot.main"]
