import os

from flask import Flask, jsonify, redirect, request
from flask_cors import CORS

from dicecloud_tools.autochar import create_char
from lib.compendium import c

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
    races = [r.name for r in c.fancyraces]
    backgrounds = [b.name for b in c.backgrounds]
    classes = []

    for klass in c.classes:
        classes.append({"name": klass['name'], "subclasses": [s['name'] for s in klass['subclasses']]})

    return jsonify({
        "races": races,
        "classes": classes,
        "backgrounds": backgrounds
    })


@app.route('/autochar', methods=["POST"])
def autochar():
    data = request.form
    api_key = data.get('apiKey')
    name = data.get('charName')
    level = data.get('level')
    race_i = data.get('race')
    klass_i = data.get('class')
    subclass_i = data.get('subclass')
    background_i = data.get('background')

    if any(d is None for d in (api_key, name, level, race_i, klass_i, background_i)):
        return redirect("https://andrew-zhu.com/dnd/dicecloudtools/autochar.html?error=MISSING_FIELD", code=302)

    race = c.fancyraces[race_i]
    klass = c.classes[klass_i]
    subclass = klass['subclasses'][subclass_i]
    background = c.backgrounds[background_i]

    try:
        new_id = create_char(api_key, name, level, race, klass, subclass, background)
    except Exception as e:
        return redirect(f"https://andrew-zhu.com/dnd/dicecloudcloner.html?error={e}", code=302)

    return redirect(f"https://dicecloud.com/character/{new_id}", code=302)


if __name__ == '__main__':
    app.run()
