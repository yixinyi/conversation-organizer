from classify.llm_models import Ollama

reply = Ollama().response_from("Say hello in one sentence.")

print(reply)
