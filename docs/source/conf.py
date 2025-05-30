# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import datetime
import os
import sys
from pathlib import Path

import toml  # type: ignore

project_root = Path("../../")
with open(project_root / "pyproject.toml") as f:
    config = toml.load(f)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
project = config["project"]["name"]
author = config["project"]["authors"][0]["name"]
year = datetime.date.today().year
copyright = f"{year}, {author}"
version = config["project"]["version"]
release = version
# autodoc
sys.path.insert(0, os.path.abspath(project_root / project))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "myst_parser",
    "sphinx.ext.coverage",
    "sphinx_multiversion",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = []  # type: ignore

language = "ja"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_title = project
html_logo = "_static/logo.png"
html_theme = "sphinx_book_theme"
html_static_path = ["_static"]


# -- autodocのスタイルの設定 ------------------------------------------------
autodoc_member_order = "alphabetical"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "private-members": True,
    "special-members": "__init__",
    "inherited-members": True,
    "show-inheritance": True,
}

# -- カバレッジレポートの設定 ------------------------------------------------
coverage_show_missing_items = True  # カバレッジが不足しているアイテムを表示


# -- Options for sphinx-multiversion -----------------------------------------

smv_tag_whitelist = r"^\d+\.\d+$"  # これにマッチしたタグを抽出
smv_branch_whitelist = r"^main$"  # これにマッチしたブランチを抽出
