FROM ubuntu:24.04

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# Install system dependencies and a Python virtual environment
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && python3.12 -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

# Install pipx and poetry
RUN python3.12 -m pip install pipx \
    && pipx ensurepath \
    && pipx install poetry==1.7.1

# Set working directory
WORKDIR /app

# Copy project files
COPY README.md pyproject.toml poetry.lock ./
COPY ddcheck ./ddcheck
COPY .streamlit ./.streamlit

# Install dependencies
ENV PATH="/root/.local/bin:$PATH"
RUN poetry install

# Expose Streamlit port
EXPOSE 8501

# Set entrypoint
ENTRYPOINT ["poetry", "run", "streamlit", "run", "ddcheck/main.py"]
