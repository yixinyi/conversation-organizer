# Multi-Vendor Conversation Organizer

This tool converts conversation exports (ChatGPT, Grok, Claude, and DeepSeek) into individual Markdown (`.md`) files suitable for use with [Obsidian](https://obsidian.md/),
where plugins like Dataview and Smart Connections offer better organization and search than the native chat interfaces.

---

### ✨ Features

**Conversion highlights:**

* Converts each conversation into a standalone Markdown file, with YAML front matter containing metadata and conversation statistics
* Re-converting a newer export updates existing notes in-place—no duplication
* Automatically includes a link to the original conversation
* Supports `.zip`, extracted export folders, and raw `.json` files
* Auto-detects supported providers, with an explicit `--provider` override
* Writes conversations into provider subfolders by default
* The name of the model (ChatGPT exports) or speaker is shown
* Renders:

  * Search tool results with URLs
  * Canvas code
  * LaTeX blocks compatible with Obsidian display

*Tip: Use Git to track and review local changes over time.*

> ⚠️ Currently, deep research links, images, audio and video content in conversations are **not supported**.

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
   python -m export.main /path/to/conversations.json /path/to/output_folder/ --provider chatgpt
   ```

   Existing flat notes are updated in place by default. To move matching legacy notes into provider subfolders:

   ```bash
   python -m export.main /path/to/export.zip /path/to/output_folder/ --migrate-layout
   ```

---

**Contributions and collaborators are welcome!**
