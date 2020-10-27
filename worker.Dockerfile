FROM python:3.9-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=ON \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

COPY ./app /app/app
COPY ./migrations /app/migrations
COPY flask_blog.py config.py boot.sh ./

RUN chmod +x boot.sh

EXPOSE 5000
ENTRYPOINT [ "rq" ]
CMD [ "worker", "-u", "redis://redis:6379", "flask_blog-tasks" ]
