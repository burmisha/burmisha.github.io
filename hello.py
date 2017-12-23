#!/usr/bin/env python
from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello_world():
    return "Hello, World!"

@app.route("/user/<string:username>")
def user(username, methods=["GET"]):
    return "Hello, {}!".format(username)

if __name__ == "__main__":
    app.run()

