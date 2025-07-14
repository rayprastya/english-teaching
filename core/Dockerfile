FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install ffmpeg
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*


# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p static media staticfiles

# Collect static files
RUN python manage.py collectstatic --noinput

# Create a startup script
RUN echo '#!/bin/bash\n\
echo "Waiting for database to be ready..."\n\
sleep 10\n\
echo "Running database migrations..."\n\
python manage.py migrate\n\
echo "Populating topics with difficulty levels..."\n\
python manage.py populate_topics\n\
echo "Starting gunicorn..."\n\
exec gunicorn --bind 0.0.0.0:3000 --workers 3 core.wsgi:application' > /app/start.sh

# Make the startup script executable
RUN chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]
