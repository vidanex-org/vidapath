from typing import List
from urllib.parse import urljoin
import requests
from pydantic import parse_obj_as

from settings import settings
from models.ai_task import AI, RunAIPayload


class Algorithm:
    def __init__(self) -> None:
        self.__url = settings.ai_service_api_endpoint
        self.__secret_key = settings.ai_service_secret_key

    def build_url(self, subpath: str):
        return urljoin(self.__url, subpath)

    def build_credential(self, data: dict):
        data["secret_key"] = self.__secret_key
        return data

    @property
    def ais(self):
        r = requests.post(
            self.build_url("/api/ai_list"), json=self.build_credential({})
        )
        if r.status_code == 200:
            return parse_obj_as(List[AI], r.json())
        else:
            raise RuntimeError(r.json()["message"])

    def run_ai(self, payload: RunAIPayload) -> str:
        r = requests.post(
            self.build_url("/api/run_ai"),
            json=self.build_credential(payload.model_dump()),
        )
        if r.status_code == 200:
            return r.json()["message"]
        else:
            raise RuntimeError(r.json()["message"])


algorithm = Algorithm()
