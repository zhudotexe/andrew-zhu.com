import logging
import os
import sys
import time
import urllib.parse

from MeteorClient import MeteorClient

from .errors import InsertFailure, LoginFailure
from .http import DicecloudHTTP

TESTING = (os.environ.get("TESTING", False) or 'test' in sys.argv)
API_BASE = "https://dicecloud.com"
SOCKET_BASE = "wss://dicecloud.com/websocket"

log = logging.getLogger(__name__)


class DicecloudClient:
    instance = None
    user_id = None

    def __init__(self, username, password, api_key, debug=False):
        self.username = username
        self.encoded_password = password.encode()
        self.meteor_client = MeteorClient(SOCKET_BASE, debug=debug)
        self.http = DicecloudHTTP(API_BASE, api_key, debug=debug)
        self.logged_in = False
        self.debug = debug

    def initialize(self):
        log.info(f"Initializing Dicecloud Meteor client (debug={TESTING})")
        self.meteor_client.connect()
        loops = 0
        while (not self.meteor_client.connected) and loops < 100:
            time.sleep(0.1)
            loops += 1
        log.info(f"Connected to Dicecloud in {loops/10} seconds")

        def on_login(error, data):
            if data:
                type(self).user_id = data.get('id')
                self.logged_in = True
            else:
                log.warning(error)
                raise LoginFailure()

        self.meteor_client.login(self.username, self.encoded_password, callback=on_login)
        loops = 0
        while not self.logged_in and loops < 100:
            time.sleep(0.1)
            loops += 1
        log.info(f"Logged in as {self.user_id}")

    def ensure_connected(self):
        if self.logged_in:  # everything is fine:tm:
            return
        self.initialize()

    def _get_list_id(self, character, list_name=None):
        """
        :param character: (Character) the character to get the spell list ID of.
        :param list_name: (str) The name of the spell list to look for. Returns default if not passed.
        :return: (str) The default list id.
        """
        if character.get_cached_spell_list_id():
            return character.get_cached_spell_list_id()
        char_id = character.id[10:]

        char = self.get_character(char_id)
        if list_name:
            list_id = next((l for l in char.get('spellLists', []) if l['name'].lower() == list_name.lower()), None)
        else:
            list_id = next((l for l in char.get('spellLists', [])), None)
        character.update_cached_spell_list_id(list_id)
        return list_id

    def get_character(self, char_id):
        return self.http.get(f'/character/{char_id}/json')

    def add_spell(self, character, spell):
        """Adds a spell to the dicecloud list."""
        return self.add_spells(character, [spell])

    def add_spells(self, character, spells, spell_list=None):
        """
        :param character: (Character) The character to add spells for.
        :param spells: (list) The list of spells to add
        :param spell_list: (str) The spell list name to search for in Dicecloud.
        """
        assert character.live
        list_id = self._get_list_id(character, spell_list)
        if not list_id:  # still
            raise InsertFailure("No matching spell lists on origin sheet. Run `!update` if this seems incorrect.")
        return self.http.post(f'/api/character/{character.id[10:]}/spellList/{list_id}',
                              [s.to_dicecloud() for s in spells])

    def create_character(self, name: str = "New Character", gender: str = None, race: str = None,
                         backstory: str = None):
        data = {'name': name, 'writers': [self.user_id]}
        if gender is not None:
            data['gender'] = gender
        if race is not None:
            data['race'] = race
        if backstory is not None:
            data['backstory'] = backstory

        data['settings'] = {'viewPermission': 'public'}  # sharing is caring!
        response = self.http.post('/api/character', data)
        return response['id']

    def delete_character(self, char_id: str):
        self.http.delete(f'/api/character/{char_id}')

    def get_user_id(self, username: str):
        username = urllib.parse.quote_plus(username)
        user_id = self.http.get(f'/api/user?username={username}')
        return user_id['id']

    def transfer_ownership(self, char_id: str, user_id: str):
        self.http.put(f'/api/character/{char_id}/owner', {'id': user_id})

    def insert_feature(self, char_id, feature):
        return (self.insert_features(char_id, [feature]))[0]

    def insert_features(self, char_id: str, features: list):
        response = self.http.post(f'/api/character/{char_id}/feature', [f.to_dict() for f in features])
        return response

    def insert_proficiency(self, char_id, prof):
        return (self.insert_proficiencies(char_id, [prof]))[0]

    def insert_proficiencies(self, char_id: str, profs: list):
        response = self.http.post(f'/api/character/{char_id}/prof', [p.to_dict() for p in profs])
        return response

    def insert_effect(self, char_id, effect):
        return (self.insert_effects(char_id, [effect]))[0]

    def insert_effects(self, char_id: str, effects: list):
        response = self.http.post(f'/api/character/{char_id}/effect', [e.to_dict() for e in effects])
        return response

    def insert_class(self, char_id, klass):
        return (self.insert_classes(char_id, [klass]))[0]

    def insert_classes(self, char_id: str, classes: list):
        response = self.http.post(f'/api/character/{char_id}/class', [c.to_dict() for c in classes])
        return response
