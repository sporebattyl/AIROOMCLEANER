FROM python:3.13-slim-bookworm
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y git && \
    pip install --no-cache-dir -r requirements.txt
COPY ./backend/ .
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]