import hashlib
import shutil
from pathlib import Path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def copy_file(src: Path, dst: Path) -> None:
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)


def copy_dir(src: Path, dst: Path) -> None:
    ensure_dir(dst.parent)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def file_exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def dir_exists(path: Path) -> bool:
    return path.exists() and path.is_dir()


def compute_md5(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.is_file():
        path.unlink()
