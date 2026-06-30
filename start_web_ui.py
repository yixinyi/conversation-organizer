import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


def get_venv_python(repo_root: Path):
    candidates = [
        repo_root / ".venv" / "bin" / "python",
        repo_root / ".venv" / "Scripts" / "python.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def main() -> None:
    python_exe = get_venv_python(REPO_ROOT)
    if python_exe is None:
        print("Creating a local virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", str(REPO_ROOT / ".venv")])
        python_exe = get_venv_python(REPO_ROOT)

    if python_exe is None:
        raise SystemExit("Could not locate the virtual environment Python interpreter.")

    print("Installing dependencies...")
    subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([python_exe, "-m", "pip", "install", "-r", str(REPO_ROOT / "requirements.txt")])
    subprocess.check_call([python_exe, "-m", "pip", "install", "-e", str(REPO_ROOT)])

    print("Starting the web UI...")
    subprocess.call([python_exe, str(REPO_ROOT / "web_ui" / "app.py")])


if __name__ == "__main__":
    main()
