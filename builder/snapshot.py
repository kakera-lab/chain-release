import argparse
import logging
import os
import shutil
import sys
import zipfile
from pathlib import Path

import pathspec
from pathspec.util import append_dir_sep

from . import settings, version

logger = logging.getLogger(__name__)


def delete_old_zips() -> None:
    for file in settings.project_root.glob("release-*.zip"):
        try:
            file.unlink()
            logger.info(f"🗑️ Removed old release: {file.name}")
        except Exception as e:
            logger.warning(f"⚠️ Could not delete {file.name}: {e}")


def create_new_zip(version_str: str) -> None:
    zip_path = settings.project_root / f"release-{version_str}.zip"
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(settings.temp_dir):
                for file in files:
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(settings.temp_dir)
                    zipf.write(full_path, arcname=rel_path)
        logger.info(f"✅ Created new release: {zip_path.name}")
    except Exception as e:
        logger.exception("❌ Failed to create zip file.")
        raise


def load_gitignore_spec() -> pathspec.PathSpec:
    if settings.gitignore.exists():
        with settings.gitignore.open("r", encoding="utf-8") as f:
            return pathspec.PathSpec.from_lines("gitwildmatch", f)
    return pathspec.PathSpec([])


def should_exclude(path: Path, spec: pathspec.PathSpec) -> bool:
    try:
        rel_path = path.relative_to(settings.project_root)
        return bool(spec.match_file(append_dir_sep(rel_path)))
    except ValueError:
        return False


def copy_with_filter(src: Path, dst: Path, spec: pathspec.PathSpec) -> None:
    if should_exclude(src, spec):
        return
    try:
        if src.is_dir():
            dst.mkdir(exist_ok=True)
            for item in src.iterdir():
                copy_with_filter(item, dst / item.name, spec)
        else:
            shutil.copy2(src, dst)
    except Exception as e:
        logger.warning(f"⚠️ Failed to copy {src}: {e}")


def prepare_release() -> None:
    if settings.temp_dir.is_dir():
        shutil.rmtree(settings.temp_dir)
    settings.temp_dir.mkdir()

    spec_gitignore = load_gitignore_spec()
    spec_tool_ignore = pathspec.PathSpec.from_lines("gitwildmatch", settings.ignore)

    for item in settings.project_root.iterdir():
        if item.name == settings.temp_dir.name or item.name.startswith(".git"):
            continue
        if should_exclude(item, spec_gitignore) or should_exclude(item, spec_tool_ignore):
            continue
        copy_with_filter(item, settings.temp_dir / item.name, spec_gitignore)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a release zip.")
    parser.add_argument("level", nargs="?", choices=settings.version_levels, help="Version bump level")
    args = parser.parse_args()

    try:
        current_version = settings.version
        new_version = current_version

        if args.level:
            new_version = version.bump_version(current_version, args.level)
            version.update_version(settings.pyproject, new_version)

        delete_old_zips()
        prepare_release()
        create_new_zip(new_version)

    except Exception as e:
        logger.exception("🚨 Release process failed.")
        sys.exit(1)
    finally:
        if settings.temp_dir.is_dir():
            shutil.rmtree(settings.temp_dir)
            logger.info("🧹 Cleaned up temporary files.")


if __name__ == "__main__":
    main()
