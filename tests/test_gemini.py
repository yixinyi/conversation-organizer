import requests
import os
import json
import ast


# Get the directory where the script is located
script_path = os.path.abspath(__file__)

script_dir = os.path.dirname(script_path)
root_dir = os.path.dirname(script_dir)

# Load config.json using the absolute path
config_path = os.path.join(root_dir, 'data', 'config.json')


with open(config_path, "r") as f:
    config = json.load(f)


# Configuration
api_key = config["api_key"]
api_url = config["api_url"]


def test_gemini_connection():
    # prompt = 'Return only a list of five animal names in the form of Python list of strings, but not actual code.'
    prompt = 'Return [] only.'
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    params = {
        "key": api_key
    }
    try:
        response = requests.post(api_url, params=params, json=payload)
        response.raise_for_status()
        candidates = response.json().get("candidates", [])
        reply = candidates[0]["content"]["parts"][0]["text"].strip()
        reply_list = ast.literal_eval(reply)
        print("✅ Gemini responded successfully!")
        print("Model's reply:", type(reply_list))
    except requests.RequestException as e:
        print("❌ Error contacting Gemini:", e)


if __name__ == "__main__":
    test_gemini_connection()
