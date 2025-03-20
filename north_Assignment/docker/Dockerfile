FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create static directories
RUN mkdir -p /app/static /app/staticfiles /app/media

# Expose port
EXPOSE 8000

# Collect static files
RUN python manage.py collectstatic --noinput

CMD ["daphne", "north_Assignment.asgi:application", "--bind", "0.0.0.0", "--port", "8000"]