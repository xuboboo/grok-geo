FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
COPY requirements-ui.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt -r requirements-ui.txt

# Copy application code
COPY skill/ ./skill/
COPY ui/ ./ui/
COPY scripts/ ./scripts/

# Create directory for runs
RUN mkdir -p /app/geo-audit-runs

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "ui/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]