import asyncio
import logging
import os
import random
import time

import requests
from MeteorClient import MeteorClient

TESTING = True if os.environ.get("TESTING") else False

log = logging.getLogger(__name__)


class DicecloudClient(MeteorClient):
    def __init__(self, username, password, *args, **kwargs):
        super().__init__('ws://dicecloud.com/websocket', *args, **kwargs)
        self.logged_in = False
        self.username = username
        self.password = password.encode()
        self.user_id = None

    def initialize(self):
        self.connect()
        loops = 0
        while not self.connected and loops < 100:
            time.sleep(0.1)
            loops += 1
        log.info(f"Connected to Dicecloud in {loops/10} seconds")

        def on_login(error, data):
            if data:
                self.user_id = data.get('id')
                self.logged_in = True
            else:
                log.warning(error)
                raise LoginFailure()

        self.login(self.username, self.password, callback=on_login)
        loops = 0
        while not self.logged_in and loops < 100:
            time.sleep(0.1)
            loops += 1
        log.info(f"Logged in as {self.user_id}")

    @staticmethod
    def generate_id():
        valid_characters = "23456789ABCDEFGHJKLMNPQRSTWXYZabcdefghijkmnopqrstuvwxyz"
        return "".join(random.choice(valid_characters) for _ in range(17))


def clone_sheet(url, username, password, api_key):
    if 'dicecloud.com' in url:
        url = url.split('/character/')[-1].split('/')[0]

    response = requests.get(f"https://dicecloud.com/character/{url}/json?key={api_key}")
    if 399 < response.status_code < 600:
        raise Exception("BAD_API_KEY")
    try:
        char_data = response.json()
    except:
        raise Exception("NO_CHAR_DATA")

    id_map = {}
    try:
        client = DicecloudClient(username, password)
        client.initialize()
    except:
        raise Exception("BAD_USER_INFO")

    remaining = 0

    def on_insert(error, result):
        nonlocal remaining
        remaining -= 1

    def insert(item):
        nonlocal remaining
        remaining += 1
        if '_id' in item and item['_id'] not in id_map.values():
            new_id = client.generate_id()
            id_map[item['_id']] = new_id
            item['_id'] = new_id
        if 'owner' in item:
            item['owner'] = client.user_id
        if 'charId' in item:
            if item['charId'] not in id_map:
                parent = char_data['characters'][0]
                insert(parent)
            item['charId'] = id_map[item['charId']]
        if 'parent' in item:
            if item['parent']['id'] not in id_map:
                parent_coll = item['parent']['collection'].lower()
                parent = next(i for i in char_data[parent_coll] if i['_id'] == item['parent']['id'])
                insert(parent)
            item['parent']['id'] = id_map[item['parent']['id']]

        try:
            client.insert(coll, item, callback=on_insert)
        except Exception:
            raise

    for coll, items in char_data.items():
        for item in items:
            if '_id' in item and item['_id'] not in id_map and item['_id'] not in id_map.values():
                insert(item)

    while remaining:
        time.sleep(0.1)

    return id_map[url]


class LoginFailure(Exception):
    pass
