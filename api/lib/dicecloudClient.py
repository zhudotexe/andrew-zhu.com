import asyncio
import logging
import os
import random
import time

from MeteorClient import MeteorClient

TESTING = True if os.environ.get("TESTING") else False

log = logging.getLogger(__name__)


class DicecloudClient(MeteorClient):
    def __init__(self, username, password, *args, **kwargs):
        super().__init__('ws://dicecloud.com/websocket', *args, **kwargs)
        self.logged_in = False
        self.username = username
        self.password = password
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


class LoginFailure(Exception):
    pass
