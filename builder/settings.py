from pathlib import Path

from git import Repo
from tomlkit import parse

project_root = Path(__file__).parent.parent
pyproject_path = project_root / "pyproject.toml"
with pyproject_path.open("r", encoding="utf-8") as f:
    pyproject = parse(f.read())

repo = Repo(".")

prj_name = pyproject.get("project", {}).get("name", "")
version = pyproject.get("project", {}).get("version", "")
version_levels = ("major", "minor", "patch")

# container
docker_cfg = pyproject.get("tool", {}).get("docker", {})
platforms = docker_cfg.get("platforms")
registry = docker_cfg.get("registry")
cache = docker_cfg.get("cache")
push = docker_cfg.get("push")
dockerfiles = pyproject.get("tool", {}).get("docker", {}).get("dockerfiles", {})

# release
gitignore = project_root / ".gitignore"
temp_dir = Path(".tmp_release")
release_cfg = pyproject.get("tool", {}).get("release", {})
readme = release_cfg.get("readme", False)
ignore = release_cfg.get("ignore", [])
