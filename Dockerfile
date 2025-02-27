# Use Python slim image as base
FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    # Chrome/Selenium specific settings
    CHROME_BIN=/usr/bin/chromium \
    CHROME_DRIVER_PATH=/usr/bin/chromedriver \
    SELENIUM_CHROME_HEADLESS=true \
    SELENIUM_CHROME_SANDBOX=false

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    gnupg2 \
    curl \
    tesseract-ocr \
    libtesseract-dev \
    # Chrome dependencies
    chromium \
    chromium-driver \
    # Additional required packages
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directories for logs and captcha attempts
RUN mkdir -p logs captcha_attempts && \
    chmod -R 755 logs captcha_attempts

# Expose the port the app runs on
EXPOSE 8000

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
