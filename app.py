from flask import Flask, render_template
import redis
import time


app = Flask(__name__)
cache = redis.Redis(host='redis_cache', port=6379, decode_responses=True)
app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')


def get_hit_count():
    retries = 5
    while True:
        try:
            return cache.incr('hits')
        except redis.exceptions.ConnectionError as exc:
            if retries == 0:
                raise exc
            retries -= 1
            time.sleep(0.5)


@app.route('/')
def hello():
    count = get_hit_count()
    return render_template('index.pug', count=count)
