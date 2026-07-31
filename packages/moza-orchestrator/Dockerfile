FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/
COPY examples/ ./examples/
COPY README.md .
COPY pyproject.toml .
COPY setup.py .
COPY config.json .

# Install the package
RUN pip install -e .

# Create non-root user
RUN useradd -m -u 1000 moza
USER moza

# Expose port (if needed for web interface)
EXPOSE 8000

# Default command
CMD ["python", "-m", "moza_orchestrator.cli", "--help"]