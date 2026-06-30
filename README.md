# Multi-Vendor Conversation Organizer

This tool converts conversation exports (ChatGPT, Grok, Claude, DeepSeek) into individual Markdown (`.md`) files suitable for use with [Obsidian](https://obsidian.md/). 

The converter focuses primarily on conversation text and metadata. Rich content such as images, videos, source references, tool outputs, and other provider-specific artifacts may not be included. A link to the original conversation is automatically included, so you can access the complete content if needed. 

---

### ✨ Features

**Conversion highlights:**

* Converts each conversation into a standalone Markdown file, with YAML front matter containing metadata and conversation statistics
* Re-converting a newer export updates existing notes in-place—no duplication
* The name of the model or speaker is shown, if the original export provides it
* Renders LaTeX blocks compatible with Obsidian display

*Tip: Use Git to track and review local changes over time.*


---

**Classification module (optional):**

* Uses an LLM (e.g., Google Gemini or Ollama-backed models) to auto-assign tags from a user-defined tag list.

**Note:** Configuration files are not tracked in version control.

* Store model API info and keys in `config/gemini.json` or `config/ollama.json`
* Store tag definitions (with descriptions) in `config/user_tags.json`



### 🌐 Web UI

A simple Flask-based web interface is included in `web_ui/app.py`.

Quick start:

1. Download the current repository 

2. Open a terminal and write (you must have python installed):

```bash
python start_web_ui.py
```

This will create a local virtual environment if needed, install the dependencies, and start the app. 

3. Then open a browser and copy the address:

```
http://127.0.0.1:5001
```

To kill the app, use the terminal:

```
lsof -i :5001  
```

and look for PID number, then:

```
kill [PID number]
```

---

**Contributions and collaborators are welcome!**
