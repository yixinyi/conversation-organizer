import requests


class Gemini:
    def __init__(self, api_key, api_url):
        self.api_key = api_key
        self.api_url = api_url

    def classify_conversation(self, prompt):
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

