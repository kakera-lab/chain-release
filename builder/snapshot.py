import os
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any

import pathspec
from pathspec.util import append_dir_sep
from tomlkit import TOMLDocument, dumps, parse

SRC_DIR = Path(".")
TMP_DIR = Path(".tmp_release")
PYPROJECT_PATH = SRC_DIR / "pyproject.toml"
VERSION_LEVELS = ("major", "minor", "patch")
GITIGNORE = SRC_DIR / ".gitignore"


def read_pyproject() -> TOMLDocument:
    with PYPROJECT_PATH.open("r", encoding="utf-8") as f:
        return parse(f.read())


def update_version(data: dict[str, Any], new_version: str) -> None:
    data["project"]["version"] = new_version
    with PYPROJECT_PATH.open("w", encoding="utf-8") as f:
        f.write(dumps(data))
    print(f"✅ Updated pyproject.toml to version {new_version}")


def bump_version(version: str, level: str) -> str:
    major, minor, patch = map(int, version.split("."))
    if level == "major":
        major += 1
        minor = 0
        patch = 0
    elif level == "minor":
        minor += 1
        patch = 0
    elif level == "patch":
        patch += 1
    else:
        raise ValueError("Invalid bump level.")
    return f"{major}.{minor}.{patch}"


def delete_old_zips() -> None:
    for file in SRC_DIR.glob("release-*.zip"):
        file.unlink()
        print(f"🗑️ Removed old release: {file.name}")


def create_zip(version: str) -> None:
    zip_name = f"release-{version}.zip"
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(TMP_DIR):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(TMP_DIR)
                zipf.write(full_path, arcname=rel_path)
    print(f"✅ Created new release: {zip_name}")


def load_gitignore_spec() -> pathspec.PathSpec:
    if GITIGNORE.exists():
        with GITIGNORE.open("r", encoding="utf-8") as f:
            return pathspec.PathSpec.from_lines("gitwildmatch", f)
    return pathspec.PathSpec([])


def get_release_config(pyproject: dict[str, Any]) -> tuple[bool, pathspec.PathSpec]:
    release_cfg = pyproject.get("tool", {}).get("release", {})
    recursive = release_cfg.get("recursive", False)
    ignore_list = release_cfg.get("ignore", [])
    spec = pathspec.PathSpec.from_lines("gitwildmatch", ignore_list)
    return recursive, spec


def should_exclude(path: Path, spec: pathspec.PathSpec) -> bool:
    try:
        rel_path = path.relative_to(SRC_DIR)
        result: bool = spec.match_file(append_dir_sep(rel_path))
        return result
    except ValueError:
        return False


def copy_with_filter(src: Path, dst: Path, spec: pathspec.PathSpec, recursive: bool) -> None:
    if should_exclude(src, spec):
        return
    if src.is_dir():
        if recursive:
            dst.mkdir(exist_ok=True)
            for item in src.iterdir():
                copy_with_filter(item, dst / item.name, spec, recursive)
        else:
            shutil.copytree(src, TMP_DIR / src.name)
    else:
        shutil.copy(src, dst)


def prepare_release(pyproject: dict[str, Any]) -> None:
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)
    TMP_DIR.mkdir()

    spec_gitignore = load_gitignore_spec()
    recursive, spec_tool_ignore = get_release_config(pyproject)

    for item in SRC_DIR.iterdir():
        if item.name == TMP_DIR.name or item.name.startswith(".git"):
            continue
        # git ignore の分は再起的
        if should_exclude(item, spec_gitignore):
            continue
        if should_exclude(item, spec_tool_ignore):
            continue
        if item.name == "README.md":
            shutil.copy(item, TMP_DIR / "README.tpl.md")
        else:
            copy_with_filter(item, TMP_DIR / item.name, spec_gitignore, recursive)


def main() -> None:
    if len(sys.argv) == 1:
        level = None
    elif len(sys.argv) == 2 and sys.argv[1] in VERSION_LEVELS:
        level = sys.argv[1]
    else:
        sys.exit(1)

    pyproject = read_pyproject()
    current_version = pyproject["project"]["version"]
    new_version = current_version
    if level:
        new_version = bump_version(current_version, level)
        update_version(pyproject, new_version)
    delete_old_zips()
    prepare_release(pyproject)
    create_zip(new_version)
    shutil.rmtree(TMP_DIR)


if __name__ == "__main__":
    main()
