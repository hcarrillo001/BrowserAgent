FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app

ENV HEADLESS=true

RUN apt-get update && apt-get install -y \
    curl nodejs npm \
    && rm -rf /var/lib/apt/lists/*

RUN npm init -y && \
    npm install playwright && \
    npm install -g @playwright/cli && \
    npx playwright install chrome && \
    npx playwright install-deps chrome

RUN pip install anthropic python-dotenv

# Create a non-root user
RUN useradd -m -u 1000 pwuser && chown -R pwuser /app
RUN chown -R pwuser /root/.cache 2>/dev/null || true

COPY aiagentcontroller.py .
COPY .env .

USER pwuser

CMD ["python", "aiagentcontroller.py"]