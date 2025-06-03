import os
import json
from classify.llm_models import Gemini

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
root_dir = os.path.dirname(script_dir)
config_path = os.path.join(root_dir, 'data', 'gemini_config.json')


with open(config_path, "r") as f:
    config = json.load(f)

api_key = config["api_key"]
api_url = config["api_url"]

reply = Gemini(api_key, api_url).response_from("Say hello in one sentence.")


print(reply)
