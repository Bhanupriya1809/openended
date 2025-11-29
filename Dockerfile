FROM python:3.11-slim

# Create app directory
WORKDIR /app

# Install system dependencies (needed for APScheduler + email + MySQL)
RUN apt-get update && apt-get install -y \
    gcc \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Set flask environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Expose internal container port  
# (your app runs on port 6000)
EXPOSE 6000

# Run using gunicorn (better than flask run)
CMD ["gunicorn", "--bind", "0.0.0.0:6000", "app:app"]
