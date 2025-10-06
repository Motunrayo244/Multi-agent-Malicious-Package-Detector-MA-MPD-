from __future__ import annotations

import base64
import json
import shutil
import zipfile
import gzip
import shutil
import tarfile

from pathlib import Path
from typing import Dict

try:
    import py7zr  # lightweight dependency; only needed for .7z
except ImportError:  # defer the error until it’s actually required
    py7zr = None

EXTRACT_ROOT = Path(".temp") / "packages"  # where we unpack wheels / zips
EXTRACT_ROOT.mkdir(parents=True, exist_ok=True)

PLAIN_ROOT   = Path(".temp") / "plain"     # single‑package JSON dumps
PLAIN_ROOT.mkdir(parents=True, exist_ok=True)



SUPPORTED_EXTS = {
    ".zip", ".whl",       # already supported
    ".tar.gz", ".tgz",    # gzip‑compressed tarballs
    ".tar.bz2",           # bzip2‑compressed tarballs
    ".gz",                # single gzip file
    ".7z",                # 7‑Zip archives
}


def _compound_suffix(path: Path) -> str:
    """Return the *effective* suffix, e.g. '.tar.gz' instead of just '.gz'."""
    name = path.name.lower()
    if name.endswith(".tar.gz"):
        return ".tar.gz"
    if name.endswith(".tar.bz2"):
        return ".tar.bz2"
    return path.suffix.lower()  # .zip, .whl, .tgz, .gz, .7z, etc.


def _base_name(path: Path, eff_suffix: str) -> str:
    """
    Strip the effective suffix for the directory / json prefix.
    E.g. 'pkg.tar.gz' → 'pkg', 'model.whl' → 'model'.
    """
    return path.name[: -len(eff_suffix)]


def read_file_raw(p: Path) -> str:
    """Return UTF‑8 text if possible; otherwise Base‑64 of the raw bytes."""
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return base64.b64encode(p.read_bytes()).decode()


def folder_to_json(src: str | Path, dst: str | Path) -> Path:
    """
    Recursively walk *src* and write one JSON at *dst*
    (adding “.json” if the caller omitted it).

    JSON structure:
        {
            "<basename>": {
                "file_path": "<relative/path>",
                "content":   "<text | base64>"
            },
            ...
        }

    Returns the Path that was written.
    """
    src, dst = Path(src).expanduser(), Path(dst).expanduser()

    if not src.is_dir():
        raise ValueError(f"Source {src} is not a directory.")

    if dst.is_dir():
        raise ValueError("Destination must be a file path, not a directory.")
        # ‑ OR ‑  build a default name instead:
        # dst = dst / f"{src.name}_dump.json"

    if dst.suffix.lower() != ".json":
        dst = dst.with_suffix(".json")

    data: Dict[str, Dict[str, str]] = {}
    for f in src.rglob("*"):
        if f.is_file():
            data[f.name] = {
                "file_path": str(f.relative_to(src)),
                "content"  : read_file_raw(f),
            }

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
    return dst


def _unpack_archive(archive_path: Path) -> Path:
    """
    Unpack *archive_path* into EXTRACT_ROOT/<basename> and dump a JSON
    description of that folder via `folder_to_json`.

    Supported extensions: .zip, .whl, .tar.gz, .tgz, .tar.bz2, .gz, .7z
    """
    if not archive_path.is_file():
        raise ValueError(f"{archive_path} does not exist on disk.")

    eff_suffix = _compound_suffix(archive_path)
    if eff_suffix not in SUPPORTED_EXTS:
        raise ValueError(
            f"Unsupported archive format {eff_suffix}. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTS))}"
        )

    base = _base_name(archive_path, eff_suffix)
    dest_dir = EXTRACT_ROOT / base
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    # --- dispatch on suffix -------------------------------------------------
    if eff_suffix in {".zip", ".whl"}:
        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(dest_dir)

    elif eff_suffix in {".tar.gz", ".tgz", ".tar.bz2"}:
        with tarfile.open(archive_path, mode="r:*") as tf:
            tf.extractall(dest_dir)

    elif eff_suffix == ".gz":
        # Treat as a single gzip‑compressed file
        out_file = dest_dir / Path(base).name
        with gzip.open(archive_path, "rb") as src, open(out_file, "wb") as dst:
            shutil.copyfileobj(src, dst)

    elif eff_suffix == ".7z":
        if py7zr is None:
            raise ModuleNotFoundError(
                "py7zr is required to extract .7z files. "
                "Install it with:  pip install py7zr"
            )
        with py7zr.SevenZipFile(archive_path, mode="r") as z:
            z.extractall(dest_dir)

    out_json = PLAIN_ROOT / f"{base}_dump.json"
    return folder_to_json(dest_dir, out_json)






