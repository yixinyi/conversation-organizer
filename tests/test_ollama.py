import requests

OLLAMA_API_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "mistral:latest"  # Replace with your model's real name


def test_ollama_connection():
    prompt = "Say hello in one sentence."

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        reply = response.json()
        print("✅ Ollama responded successfully!")
        print("Model's reply:", reply["message"]["content"])
    except requests.RequestException as e:
        print("❌ Error contacting Ollama:", e)


if __name__ == "__main__":
    test_ollama_connection()
