import os
# from redis import Redis
import redis
from rq import Queue, Connection, Worker
# from rq.worker import HerokuWorker as Worker
# from urllib.parse import urlparse


# listen = ['high', 'default', 'low']
listen = ['flask_blog-tasks']

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
# if not redis_url:
#     raise RuntimeError('Set up Redis To Go first.')


# url = urlparse(redis_url)
# conn = Redis(host=url.hostname, port=url.port, db=0, password=url.password)

conn = redis.from_url(redis_url)


if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()


# rq_worker:
#     build: .
#     image: flask_app
#     container_name: rq_worker
#     env_file: .env
#     depends_on:
#         - redis
#     networks:
#         flask_blog:
#             aliases:
#                 - rq_worker
#     entrypoint: rq
#     command: worker -u ${REDIS_URL} flask_blog-tasks
