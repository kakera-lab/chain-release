import logging

import coverage
import pytest
from sphinx.cmd.build import main as sphinx_build
from sphinx.ext.apidoc import main as sphinx_apidoc

from . import settings

logger = logging.getLogger(__name__)


def run_tests_with_coverage() -> None:
    cov = coverage.Coverage()
    try:
        cov.start()
        logger.info("🧪 Running tests...")
        result = pytest.main([str(settings.project_root / "tests")])
        if result != 0:
            logger.warning(f"⚠️ Some tests failed (exit code: {result})")
    except Exception as e:
        logger.exception("❌ Error during test execution")
        raise
    finally:
        cov.stop()
        cov.save()
        html_report_dir = settings.project_root / "docs" / "coverage"
        html_report_dir.mkdir(parents=True, exist_ok=True)
        cov.html_report(directory=str(html_report_dir))
        logger.info(f"✅ Coverage report generated at: {html_report_dir}")


def generate_sphinx_docs() -> None:
    try:
        apidoc_output = settings.project_root / "docs" / "source" / "apis"
        src_path = settings.project_root / settings.prj_name

        logger.info("🛠️ Generating API documentation with sphinx-apidoc...")
        sphinx_apidoc(["-f", "-o", str(apidoc_output), str(src_path)])

        logger.info("📚 Building HTML documentation with sphinx-build...")
        sphinx_build(
            [
                "-b",
                "html",
                str(settings.project_root / "docs" / "source"),
                str(settings.project_root / "docs" / "build"),
            ]
        )
        logger.info("✅ Sphinx documentation built successfully.")

    except Exception as e:
        logger.exception("❌ Error during documentation generation")
        raise


def main() -> None:
    try:
        run_tests_with_coverage()
        generate_sphinx_docs()
    except Exception:
        logger.error("🚨 Documentation pipeline failed.")
    else:
        logger.info("🏁 All steps completed successfully.")
    finally:
        logger.info("🎬 Process finished.")


if __name__ == "__main__":
    main()
