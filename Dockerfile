# Multi-stage build for optimized image
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 torah_user

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/torah_user/.local

# Copy application code
COPY --chown=torah_user:torah_user . .

# Make scripts executable and create instance directory with proper permissions
RUN chmod +x start.sh && \
    mkdir -p /app/instance && \
    chown -R torah_user:torah_user /app/instance && \
    chmod 755 /app/instance

# Switch to non-root user
USER torah_user

# Add local bin to PATH
ENV PATH=/home/torah_user/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Run gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]
