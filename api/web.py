import os

from flask import Flask, jsonify, redirect
from flask_cors import CORS

TESTING = True if os.environ.get("TESTING") else False

app = Flask(__name__)
CORS(app)


@app.route('/', methods=["GET"])
def hello_world():
    return 'Hello World!'


@app.route('/dicecloudcloner', methods=["POST"])
def clone_dicecloud():
    return redirect("https://andrew-zhu.com/dnd/dicecloudcloner.html?error=TOOL_REMOVED", code=302)


@app.route('/autochar_options', methods=["GET"])
def autochar_options():
    return jsonify({
        "races": ["asdf", "foo"],
        "classes": [
            {
                "name": "potato",
                "subclasses": []
            },
            {
                "name": "tomato",
                "subclasses": ["salsa"]
            }
        ],
        "backgrounds": ["a", "b"]
    })


if __name__ == '__main__':
    app.run()
