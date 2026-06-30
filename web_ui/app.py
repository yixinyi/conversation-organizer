"""
Simple web UI for the conversation export tool.

Usage:
    cd conversation-organizer-main
    source venv/bin/activate
    python web_ui/app.py

Then open http://127.0.0.1:5001 in your browser.
"""

import sys
import json
import tempfile
from pathlib import Path

# Add parent directory so we can import from export/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename

from export.chatgpt_converter import update_all_files as update_chatgpt
from export.grok_converter import update_all_files as update_grok
from export.claude_converter import update_all_files as update_claude
from export.deepseek_converter import update_all_files as update_deepseek
from export.zip_processor import process_zip, cleanup_tempdir

app = Flask(__name__)
app.secret_key = "conversation-organizer-web-ui-secret"

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROVIDERS = {
    "chatgpt": ("ChatGPT", update_chatgpt),
    "grok": ("Grok", update_grok),
    "claude": ("Claude", update_claude),
    "deepseek": ("DeepSeek", update_deepseek),
}

UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "conversation_organizer_uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


def _file_hashes(directory: Path) -> dict:
    """Return a dict mapping filename to content hash for all files in directory."""
    import hashlib
    hashes = {}
    if not directory.exists():
        return hashes
    for fpath in directory.iterdir():
        if fpath.is_file():
            try:
                hashes[fpath.name] = hashlib.md5(fpath.read_bytes()).hexdigest()
            except OSError:
                pass
    return hashes


def run_conversion(json_path: Path, provider: str, output_dir: Path) -> list:
    """
    Run the conversion and return a list of file paths that were
    created or modified.
    """
    with json_path.open("r", encoding="utf-8") as f:
        conversations_data = json.load(f)

    # Snapshot content hashes before conversion so we can detect
    # both newly created files AND files that were updated in-place.
    before_hashes = _file_hashes(output_dir) if output_dir.exists() else {}

    converter_func = PROVIDERS[provider][1]
    converter_func(conversations_data, output_dir)

    # Compare after: files that are new or whose content changed
    after_hashes = _file_hashes(output_dir)
    changed_files = []
    for fname, after_hash in after_hashes.items():
        before_hash = before_hashes.get(fname)
        if before_hash is None or before_hash != after_hash:
            changed_files.append(output_dir / fname)

    return sorted(changed_files)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # ── Check if this is the second POST (conversion phase) ──────────
        json_path_str = request.form.get("json_path", "").strip()
        extract_dir_str = request.form.get("extract_dir", "").strip()

        if json_path_str and extract_dir_str:
            # ── Second POST: run conversion ─────────────────────────
            json_path = Path(json_path_str)
            extract_dir = Path(extract_dir_str)

            provider = request.form.get("provider")
            if provider not in PROVIDERS:
                flash("Invalid provider selected.", "error")
                cleanup_tempdir(extract_dir)
                return redirect(url_for("index"))

            # Get and validate output directory
            output_dir_raw = request.form.get("output_dir", "").strip()
            if not output_dir_raw:
                flash("Please specify a folder to save the converted files.", "error")
                cleanup_tempdir(extract_dir)
                return redirect(url_for("index"))

            output_dir = Path(output_dir_raw)
            # If only a single path component (no separators), resolve relative to PROJECT_ROOT
            if output_dir.parent == Path("."):
                output_dir = PROJECT_ROOT / output_dir_raw
            output_dir = output_dir.expanduser().resolve()
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError) as e:
                flash(f"Cannot create or write to the specified folder: {e}", "error")
                cleanup_tempdir(extract_dir)
                return redirect(url_for("index"))

            try:
                created_files = run_conversion(json_path, provider, output_dir)
                provider_label = PROVIDERS[provider][0]
                file_count = len(created_files)
                # Cleanup temp dir after successful conversion
                cleanup_tempdir(extract_dir)
                return render_template(
                    "result.html",
                    file_count=file_count,
                    provider=provider_label,
                    files=[f.name for f in created_files],
                    output_dir=str(output_dir),
                )
            except Exception as e:
                flash(f"Error during conversion: {e}", "error")
                cleanup_tempdir(extract_dir)
                return redirect(url_for("index"))

        # ── First POST: upload zip and detect provider ──────────────
        if "zip_file" not in request.files:
            flash("No file selected.", "error")
            return redirect(url_for("index"))

        file = request.files["zip_file"]
        if file.filename == "":
            flash("No file selected.", "error")
            return redirect(url_for("index"))

        if file.filename is None:
            flash("Invalid file name.", "error")
            return redirect(url_for("index"))

        # Save uploaded zip
        filename = secure_filename(file.filename)
        if not filename.lower().endswith(".zip"):
            flash("Please upload a .zip file.", "error")
            return redirect(url_for("index"))

        zip_path = UPLOAD_FOLDER / filename
        file.save(str(zip_path))

        # Process the zip to detect provider and extract JSON
        try:
            detected_provider, json_path, extract_dir = process_zip(zip_path)
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("index"))
        except Exception as e:
            flash(f"Error processing zip file: {e}", "error")
            return redirect(url_for("index"))
        finally:
            # Remove the uploaded zip (no longer needed)
            if zip_path.exists():
                zip_path.unlink()

        if detected_provider is None or json_path is None:
            flash(
                "Could not automatically detect the provider from this zip file. "
                "Please select the provider manually and upload the file again.",
                "warning",
            )
            # Clean up the temp dir since we can't proceed with it
            if extract_dir:
                cleanup_tempdir(extract_dir)
            return render_template(
                "index.html",
                providers=PROVIDERS,
                project_root=str(PROJECT_ROOT),
            )

        # Provider detected — re-render the form with pre-selected values
        provider_label = PROVIDERS[detected_provider][0]
        flash(f"Detected provider: {provider_label}. Change if incorrect and click Convert.", "info")
        default_output_dir = str(PROJECT_ROOT / detected_provider)
        return render_template(
            "index.html",
            providers=PROVIDERS,
            project_root=str(PROJECT_ROOT),
            detected_provider=detected_provider,
            json_path=str(json_path),
            extract_dir=str(extract_dir),
            default_output_dir=default_output_dir,
            original_filename=filename,
        )

    # GET request
    return render_template("index.html", providers=PROVIDERS, project_root=str(PROJECT_ROOT))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)