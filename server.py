#!/usr/bin/env python3

from gunicorn_server import StandaloneApplication
from flask import Flask
import multiprocessing

app = Flask(__name__)


@app.route("/")
def ok():
    return "OK"

if __name__ == "__main__":
    gunicorn_app = StandaloneApplication(app, options={
        'bind': '127.0.0.1:8080',
        'workers': (multiprocessing.cpu_count() * 2) + 1,
    })
    gunicorn_app.run()
