# Pull base image
FROM python:3.12.2-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install Poetry
RUN apt-get update && apt-get install -y curl && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Create and set work directory called `app`
RUN mkdir -p /code
WORKDIR /code

# Copy the `pyproject.toml` and `poetry.lock` files
COPY pyproject.toml poetry.lock /code/

# Install dependencies with Poetry
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi && \
    rm -rf /root/.cache/

# Copy the application code
COPY . /code/

# Expose port 8002
EXPOSE 8002
