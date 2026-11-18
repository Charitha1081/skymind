FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py questions.yaml ./

# Run as an ordinary user, not root.
RUN useradd --create-home --uid 10001 skymind
USER skymind

EXPOSE 8000
# PORT: set by hosting platforms (Render uses 10000); 8000 locally.
# FORWARDED_ALLOW_IPS: which proxy may report the visitor's real address (set to * behind Render's proxy).
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WORKERS:-1} --no-server-header --proxy-headers --forwarded-allow-ips \"${FORWARDED_ALLOW_IPS:-127.0.0.1}\""]
