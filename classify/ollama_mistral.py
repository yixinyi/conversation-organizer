import requests
from pathlib import Path


# Configuration
OLLAMA_API_URL = "http://localhost:11434/api/chat" # Replace with your Ollama API endpoint
CATEGORIES = ["Job", "Gardening", "Health", "Recipe", "Finance", "AI", "Coding", "House improvement", "Physics", "School", "Math", "Publication", "Advice", "Writing"]  # Example categories
FOLDER_PATH = "Conversations"  # Folder where markdown files are stored


def classify_conversation(text):
    prompt = (
        f"Classify the following conversation into one of the categories: {', '.join(CATEGORIES)}.\n"
        f"Conversation:\n{text}\n"
        "Respond with only the category name."
    )

    payload = {
        "model": "mistral:latest",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        result = response.json().get("message", {}).get("content", "").strip()
        if not result:
            return None
        if result not in CATEGORIES:
            return None
        return result
    except requests.RequestException as e:
        print(f"Error contacting LLM: {e}")
        return None










