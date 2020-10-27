import os
import redis
from rq import Queue, Connection, Worker


listen = ['flask_blog-tasks']

redis_url = os.getenv('REDISTOGO_URL', None)
if not redis_url:
    raise RuntimeError('Set up Redis To Go first.')

conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
