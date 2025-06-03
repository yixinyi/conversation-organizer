import os
import json
from classify.llm_models import Ollama


script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
root_dir = os.path.dirname(script_dir)
config_path = os.path.join(root_dir, 'config', 'ollama.json')


with open(config_path, "r") as f:
    config = json.load(f)

api_url = config["api_url"]
model = config["model"]

reply = Ollama(api_url, model).response_from("Say hello in one sentence.")


print(reply)
