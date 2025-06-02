FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Set work directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies (don't install the project itself)
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-root

# Copy app code
COPY catkin ./catkin

# Expose port
EXPOSE 5000

# Default command (overridden in docker-compose)
CMD ["poetry", "run", "uvicorn", "catkin.src.app:app", "--host", "0.0.0.0", "--port", "5000"]