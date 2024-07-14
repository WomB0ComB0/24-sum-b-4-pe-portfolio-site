# syntax=docker/dockerfile:1

# Use a specific Python version (3.12.4 in this case)
ARG PYTHON_VERSION=3.12.4
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-privileged user that the app will run under.
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Copy the requirements file into the container.
COPY requirements.txt .

# Install dependencies
RUN apt-get update && apt-get install -y build-essential libffi-dev
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install flask gunicorn requests python-dotenv

# Copy the .env.example file into the container and rename it to .env
COPY .env.example .env

# Switch to the non-privileged user to run the application.
USER appuser

# Copy the source code into the container.
COPY . .

# Expose the port that the application listens on.
EXPOSE 8080

# Set FLASK_APP environment variable
ENV FLASK_APP=main

# Run the application.
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8080", "--reload"]