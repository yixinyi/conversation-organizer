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

### ⚠️ Configuration (Not Tracked by Git)

The `config/` folder contains user-specific settings.

**You must create it manually** with the following files:

```
config/
├── gemini.json         
├── ollama.json         
├── user_tags.json      
```
where:

`gemini.json`:

```json
{
  "api_key": "your-gemini-api-key",
  "api_url": "api_url"
}
```

`ollama.json`:

```json
{
  "model": "your-local-model",
  "api_url": "api_url"
}
```
`user_tags.json`:

```json
{
  "tag_1": "description of tag_1",
  "tag_2": "description of tag_2",
  "tag_n": "description of tag_n",
}
```