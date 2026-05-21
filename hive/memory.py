import json
import os
from pathlib import Path


RUNS_DIR = Path(__file__).parent / "runs"


def init_run(run_id: str) -> Path:
    """Create run directory and return its path."""
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def save_json(run_dir: Path, filename: str, data: dict | list):
    """Write a JSON file into the run directory."""
    path = run_dir / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[memory] Saved {filename}")


def load_json(run_dir: Path, filename: str) -> dict | list | None:
    """Read a JSON file from run directory. Returns None if missing."""
    path = run_dir / filename
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def list_runs() -> list[str]:
    """List all past run IDs, newest first."""
    if not RUNS_DIR.exists():
        return []
    runs = sorted(RUNS_DIR.iterdir(), key=os.path.getmtime, reverse=True)
    return [r.name for r in runs if r.is_dir()]
