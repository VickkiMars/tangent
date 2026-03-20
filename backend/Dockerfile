FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . .

# Copy entrypoint.sh if needed, or define CMD
# Railway prefers CMD or Start Command in UI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
