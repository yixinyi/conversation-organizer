# ChatGPT Conversation Organizer

This is a work-in-progress project. 
It converts exported ChatGPT conversations into clean, searchable Markdown notes—perfect for use with tools like **Obsidian**. 
So far, it includes:

### 1. `converter.py`

Converts the official `conversations.json` export from ChatGPT into individual `.md` files with:

* YAML front matter
* Proper Markdown formatting
* LaTeX math mode conversion (`\(...\)` → `$...$`, `\[...\]` → `$$...$$`)


### 2. `classifier.py`

Uses an LLM (e.g., Gemini or your offline models via Ollama) to enhance each Markdown file by:

* Suggesting a clearer or more descriptive title
* Choosing from user-defined tags and generating new tags 
* Updating the YAML front matter accordingly

