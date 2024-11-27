FROM python:3.12.7-slim

# defaulting, unless we add this to package deps?
ARG uvicorn_version=0.32.1
ARG fastapi_version=0.115.5

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8080 \
    WORKERS=4

# Install build dependencies & api essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && pip install --upgrade pip setuptools wheel \
    && pip install "fastapi==${fastapi_version}" "uvicorn[standard]==${uvicorn_version}" \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app
COPY . .

RUN python -m pip install -e . --root-user-action ignore

CMD ["sh", "-c", "uvicorn main:app --host $HOST --port $PORT --workers $WORKERS"]