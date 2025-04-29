FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN set -eux; \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        wget gnupg unzip \
        fonts-ipafont fonts-ipaexfont \
        xvfb ca-certificates && \
    # add Google Chrome repo & install
    wget -qO- https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
        > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN set -eux; \
    CHROME_MAJOR="$(google-chrome --version | awk '{print $3}' | cut -d. -f1)" && \
    CHROMEDRIVER_VERSION="$(wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR}" || echo "114.0.5735.90")" && \
    wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/ && chmod +x /usr/local/bin/chromedriver && \
    rm chromedriver_linux64.zip

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p profiles/niijima queue debug

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV DISPLAY=:99

# Default command
CMD ["python", "-m", "bot.main"]
