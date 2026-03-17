# --- Stage 1: Build Frontend ---
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy frontend package files and install dependencies
COPY nagent/package.json nagent/yarn.lock* nagent/package-lock.json* ./nagent/
RUN cd nagent && npm install

# Copy the rest of the frontend source code and build
COPY nagent/ ./nagent/
RUN cd nagent && npm run build


# --- Stage 2: Setup Backend ---
FROM python:3.11-slim AS backend-base

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --timeout=120 --retries=5 -r requirements.txt

# Copy backend source code
COPY backend/ .

# Copy built frontend from the previous stage
COPY --from=frontend-builder /app/nagent/dist ./static

# Copy entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the port the app runs on
EXPOSE 8000

# Run migrations once then start gunicorn
ENTRYPOINT ["/entrypoint.sh"]