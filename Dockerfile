# Use Python 3.12 slim as base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot.py .

# Expose port (optional, for webhooks)
EXPOSE 8080

# Command to run the bot
CMD ["python", "bot.py"]
