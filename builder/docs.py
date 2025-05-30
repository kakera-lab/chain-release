import logging
from pathlib import Path

import coverage
import pytest
import toml  # type: ignore
from sphinx.cmd.build import main as sphinx_build
from sphinx.ext.apidoc import main as sphinx_apidoc

logger = logging.getLogger(__name__)


def main() -> None:
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"
    pyproject = toml.load(pyproject_path)
    try:
        logger.info("Running tests with coverage...")
        cov = coverage.Coverage()
        cov.start()
        pytest.main([str(project_root / "tests")])
        cov.stop()
        cov.save()
        cov.html_report(directory=str(project_root / "docs/coverage"))
        logger.info("Generating API documentation...")
        sphinx_apidoc(
            [
                "-f",
                "-o",
                str(project_root / "docs/source/apis"),
                str(project_root / pyproject["project"]["name"]),
            ]
        )
        logger.info("Building HTML documentation with Sphinx...")
        sphinx_build(["-b", "html", "docs/source", "docs/build"])

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Process completed.")


if __name__ == "__main__":
    main()
