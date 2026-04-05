FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DJANGO_SETTINGS_MODULE=petmatch.settings

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN addgroup --system app && adduser --system --group app
RUN chown -R app:app /app
RUN chmod +x /app/entrypoint.sh
RUN python manage.py collectstatic --noinput

USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz/').getcode()" || exit 1
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "petmatch.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]