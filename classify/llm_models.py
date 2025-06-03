import requests
from abc import ABC, abstractmethod


class LLM(ABC):
    @abstractmethod
    def response_from(self, prompt: str) -> str:
        pass


class Gemini(LLM):
    def __init__(self, api_key, api_url):
        self.api_key = api_key
        self.api_url = api_url

    def response_from(self, prompt):
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        params = {
            "key": self.api_key
        }

        try:
            response = requests.post(self.api_url, params=params, json=payload)
            response.raise_for_status()
            candidates = response.json().get("candidates", [])
            if not candidates:
                return None
            reply = candidates[0]["content"]["parts"][0]["text"].strip()
            return reply

        except requests.RequestException as e:
            print(f"Error contacting Gemini: {e}")
            return None


class Ollama(LLM):
    def __init__(self, api_url, model):
        self.api_url = api_url
        self.model = model

    def response_from(self, prompt):
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            reply = response.json().get("message", {}).get("content", "").strip()
            if not reply:
                return None
            return reply
        except requests.RequestException as e:
            print(f"Error contacting LLM: {e}")
            return None
