import os

from flask import Flask, request, redirect

from lib.dicecloudClient import clone_sheet

TESTING = True if os.environ.get("TESTING") else False

app = Flask(__name__)


@app.route('/', methods=["GET"])
def hello_world():
    return 'Hello World!'


@app.route('/dicecloudcloner', methods=["POST"])
def clone_dicecloud():
    data = request.form
    username = data.get('username')
    password = data.get('password')
    api_key = data.get('apiKey')
    url = data.get('charUrl')

    if any(d is None for d in (username, password, api_key, url)):
        return redirect("https://andrew-zhu.com/dnd/dicecloudcloner.html?error=MISSING_FIELD", code=302)

    try:
        new_id = clone_sheet(url, username, password, api_key)
    except Exception as e:
        return redirect(f"https://andrew-zhu.com/dnd/dicecloudcloner.html?error={e}", code=302)

    return redirect(f"https://dicecloud.com/character/{new_id}", code=302)


if __name__ == '__main__':
    app.run()
