import flask
from flask import request, jsonify


app = flask.Flask(__name__)


@app.route('/documents', methods=['POST'])
def store_document():
    pass