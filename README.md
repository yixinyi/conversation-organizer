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

---

### 🔧 Installation

1. Clone or download this repository.

2. From the project root, install the package:

   ```bash
   pip install -e .
   ```

3. Run the converter with:

   ```bash
   python -m export.main /path/to/export.zip /path/to/output_folder/
   ```

   To force a provider or convert a raw JSON file:

   ```bash
   python -m export.main /path/to/conversations.json /path/to/output_folder/ 
   ```

   Existing flat notes are updated in place by default. To move matching legacy notes into provider subfolders:

   ```bash
   python -m export.main /path/to/export.zip /path/to/output_folder/ --migrate-layout
   ```

---

**Contributions and collaborators are welcome!**
