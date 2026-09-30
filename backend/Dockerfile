FROM python:3.11-slim

# Run the application as an unprivileged user
RUN useradd --create-home --shell /usr/sbin/nologin appuser

# Prevent Python from writing .pyc files and enable real-time logging
ENV PYTHONUNBUFFERED=1

# Install system dependencies required for PostgreSQL (psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the application files required at runtime
COPY app.py ./

USER appuser

EXPOSE 5000

CMD ["python", "app.py"]
