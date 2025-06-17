# Stage 1: Build Frontend
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Setup Backend
FROM python:3.13-slim-bookworm
WORKDIR /app
COPY --from=frontend /app/frontend/dist ./frontend/dist
COPY backend/ /app/backend
WORKDIR /app/backend
RUN apt-get update && apt-get install -y git && \
    pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]