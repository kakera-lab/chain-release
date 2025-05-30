import logging
from typing import Any

from tomlkit import dumps

from . import settings

logger = logging.getLogger(__name__)


def bump_version(version: str, level: str) -> str:
    try:
        major, minor, patch = map(int, version.strip().split("."))
    except Exception as e:
        raise ValueError(f"Invalid version format '{version}'. Expected format: 'X.Y.Z'") from e

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
        raise ValueError(f"Invalid bump level '{level}'. Expected one of: major, minor, patch")

    return f"{major}.{minor}.{patch}"


def update_version(data: dict[str, Any], new_version: str) -> None:
    try:
        data["project"]["version"] = new_version
        with settings.pyproject_path.open("w", encoding="utf-8") as f:
            f.write(dumps(data))
        logger.info(f"✅ Updated pyproject.toml to version {new_version}")
    except Exception as e:
        logger.exception("❌ Failed to update pyproject.toml")
        raise


if __name__ == "__main__":
    pass
