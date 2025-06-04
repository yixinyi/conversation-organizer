from classify.llm_models import Gemini

reply = Gemini().response_from("Say hello in one sentence.")

print(reply)
