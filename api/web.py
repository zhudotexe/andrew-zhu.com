import json
import os
import traceback

from flask import Flask, jsonify, redirect, request
from flask_cors import CORS

from dicecloud_tools.autochar import create_char
from lib.compendium import c
from lib.dicecloud.client import DicecloudClient

TESTING = True if os.environ.get("TESTING") else False

app = Flask(__name__)
CORS(app)


@app.route('/', methods=["GET"])
def hello_world():
    return 'Hello World!'


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
    try:
        level = int(data.get('level'))
        race_i = int(data.get('race'))
        klass_i = int(data.get('class'))
        subclass_i = int(data.get('subclass'))
        background_i = int(data.get('background'))
    except (ValueError, TypeError):
        return redirect("https://andrew-zhu.com/dnd/dicecloudtools/autochar.html?error=MISSING_FIELD", code=302)

    race = c.fancyraces[race_i]
    klass = c.classes[klass_i]
    subclass = klass['subclasses'][subclass_i]
    background = c.backgrounds[background_i]

    try:
        new_id = create_char(api_key, name, level, race, klass, subclass, background)
    except Exception as e:
        return redirect(f"https://andrew-zhu.com/dnd/dicecloudtools/autochar.html?error={e}", code=302)

    return redirect(f"https://dicecloud.com/character/{new_id}", code=302)


@app.route('/spell_options', methods=["GET"])
def spell_options():
    spells = []
    for i, spell in enumerate(c.spells):
        spells.append({"name": spell.name, "classes": "".join(spell.classes).lower(), "level": spell.level, "index": i})

    return jsonify(spells)


@app.route('/spellbook', methods=["POST"])
def spellbook():
    data = request.get_json()
    api_key = data.get('apiKey')
    url = data.get('charURL')
    if 'dicecloud.com' in url:
        url = url.split('/character/')[-1].split('/')[0]
    spells = data.get('spells')
    try:
        spells = [c.spells[s['index']] for s in spells]
        if not spells:
            raise Exception("You are not inserting any spells.")
        dc = DicecloudClient(None, None, api_key, no_meteor=True)
        dc.add_spells(url, spells)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})
    return jsonify({"success": True, "inserted": len(spells)})


if __name__ == '__main__':
    app.run()
