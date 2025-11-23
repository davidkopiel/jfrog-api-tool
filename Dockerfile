# Use a slim Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# --- Install system build dependencies ---
# 'cryptography' needs these to compile successfully
RUN apt-get update && \
    apt-get install -y --fix-broken && \
    apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Upgrade pip to the latest version (fixes many wheel issues)
RUN pip install --upgrade pip

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Install the tool globally
RUN pip install .

# Keep alive
CMD ["tail", "-f", "/dev/null"]