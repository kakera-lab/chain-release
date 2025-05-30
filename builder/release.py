import shutil
from pathlib import Path
from typing import Any

from git import Repo
from tomlkit import parse

REPO = Repo(".")
SRC_DIR = Path(".")
PYPROJECT_PATH = SRC_DIR / "pyproject.toml"


def get_release_config() -> Any:
    with PYPROJECT_PATH.open("r", encoding="utf-8") as f:
        pyproject = parse(f.read())
    release_cfg = pyproject.get("tool", {}).get("release", {})
    return release_cfg.get("ignore", [])


def main(main: str = "main", release: str = "release") -> None:
    REPO.git.checkout(main)
    REPO.remotes.origin.fetch()
    branch_list = [ref.name for ref in REPO.remotes.origin.refs]

    if f"origin/{release}" in branch_list:
        if release in REPO.heads:
            REPO.git.checkout(release)
        else:
            REPO.git.checkout("-b", release, "--track", f"origin/{release}")
    else:
        REPO.git.checkout("-b", release)

    try:
        REPO.git.merge(f"origin/{main}")
        print(f"✅ Merged {main} into {release}")
    except Exception as e:
        print(f"⚠️ Merge conflict or error: {e}")

    for file_path in get_release_config():
        path = SRC_DIR / file_path
        if path.is_dir():
            shutil.rmtree(path)
            REPO.index.remove([file_path], r=True)
            print(f"Deleted directory {file_path}")
        elif path.is_file():
            path.unlink()
            REPO.index.remove([file_path])
            print(f"Deleted file {file_path}")
    old_path = SRC_DIR / "README.md"
    new_path = SRC_DIR / "README.tpl.md"
    if old_path.exists():
        old_path.rename(new_path)
        REPO.index.remove([old_path])
        REPO.index.add([new_path])
        print(f"Renamed {old_path} to {new_path}")

    REPO.index.commit(f"Update branch '{release}'")
    print(f"Updated and committed changes on branch '{release}'")

    REPO.remotes.origin.push(refspec=f"{release}:{release}")
    print(f"Pushed changes to origin/{release}")


if __name__ == "__main__":
    main()
