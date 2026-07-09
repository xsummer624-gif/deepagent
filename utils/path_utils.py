from pathlib import Path
from typing import Optional


def resolve_path(filename: str, session_dir: Optional[str] = None) -> str:
    if not session_dir:
        return str(Path(filename).resolve())
    return str(Path(session_dir).resolve() / filename)
