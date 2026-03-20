# --- Stage 1: Build Frontend ---
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy frontend package files and install dependencies
COPY frontend/package.json frontend/yarn.lock* frontend/package-lock.json* ./frontend/
RUN cd frontend && npm install

# Copy the rest of the frontend source code and build
COPY frontend/ ./frontend/
RUN cd frontend && npm run build


# --- Stage 2: Setup Backend ---
FROM python:3.11-slim AS backend-base

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --timeout=120 --retries=5 -r requirements.txt

# Copy backend source code
COPY backend/ .

# Copy built frontend from the previous stage
COPY --from=frontend-builder /app/frontend/dist ./static

# Copy entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the port the app runs on
EXPOSE 8000

# Run migrations once then start gunicorn
ENTRYPOINT ["/entrypoint.sh"]