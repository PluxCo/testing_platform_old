import os

import requests


class Settings:
    def __init__(self, pin: str):
        self.pin = pin


class SettingsDAO:
    __resource = '{}/settings/'
    __host = os.getenv("TELEGRAM_URL", "http://localhost:3001")

    @staticmethod
    def set_host(resource: str):
        SettingsDAO.__host = resource

    @staticmethod
    def _construct(resp):
        q = Settings(resp['pin'])
        return q

    @staticmethod
    def get_settings() -> Settings:
        resp = requests.get(SettingsDAO.__resource.format(SettingsDAO.__host)).json()
        return SettingsDAO._construct(resp)

    @staticmethod
    def update_settings(settings: Settings):
        req = {"pin": settings.pin}

        resp = requests.post(SettingsDAO.__resource.format(SettingsDAO.__host), json=req)
