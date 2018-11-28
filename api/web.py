import os

import requests
from flask import Flask, request, redirect

from lib.dicecloudClient import DicecloudClient

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
        return redirect("https://andrew-zhu.com/dnd/dicecloudcloner.html?success=0", code=302)

    if 'dicecloud.com' in url:
        url = url.split('/character/')[-1].split('/')[0]

    response = requests.get(f"https://dicecloud.com/character/{url}/json?key={api_key}")
    if 399 < response.status_code < 600:
        return redirect("https://andrew-zhu.com/dnd/dicecloudcloner.html?success=0", code=302)

    id_map = {}
    try:
        client = DicecloudClient(username, password)
        client.initialize()
        char_data = response.json()
    except:
        return redirect("https://andrew-zhu.com/dnd/dicecloudcloner.html?success=0", code=302)

    for coll, items in char_data.items():
        for item in items:
            if '_id' in item and item['_id'] not in id_map.values():
                new_id = client.generate_id()
                id_map[item['id']] = new_id
                item['_id'] = new_id
            if 'owner' in item:
                item['owner'] = client.user_id
            if 'charId' in item:
                if item['charId'] not in id_map:
                    new_id = client.generate_id()
                    id_map[char_data['characters'][0]['_id']] = new_id
                    char_data['characters'][0]['_id'] = new_id
                item['charId'] = id_map[item['charId']]
            if 'parent' in item:
                if item['parent']['id'] not in id_map:
                    new_id = client.generate_id()
                    parent_coll = item['parent']['collection'].lower()
                    parent = next(i for i in char_data[parent_coll] if i['_id'] == item['parent']['id'])
                    id_map[parent['_id']] = new_id
                    parent['_id'] = new_id
                item['parent']['id'] = id_map[item['parent']['id']]

            client.insert(coll.lower(), item)

    return redirect(f"https://dicecloud.com/character/{id_map[url]}", code=302)


if __name__ == '__main__':
    app.run()
