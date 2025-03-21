"""
Sphinx configuration for TorrentDirectories documentation.
"""

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
from datetime import datetime
from typing import List

sys.path.insert(0, os.path.abspath(".."))

project = "TorrentDirectories"
copyright = f"{datetime.now().year}, friedhardware"
author = "friedhardware"

version = "1.0"
release = "1.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # Automatically include docstrings
    "sphinx.ext.napoleon",  # Support for NumPy and Google style docstrings
    "sphinx.ext.intersphinx",  # Link to other project's documentation
    "sphinx.ext.viewcode",  # Add links to highlighted source code
    "sphinx.ext.coverage",  # Check documentation coverage
    "sphinx.ext.githubpages",  # Create .nojekyll file for GitHub Pages
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "en"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_favicon = "_static/images/favicon.ico"

# These paths are either relative to html_static_path or fully qualified paths (eg. https://...)
html_css_files: List[str] = []

html_theme_options = {
    # Display
    "style_nav_header_background": "#2980B9",  # Classic Read the Docs blue
    "logo_only": False,
    # Navigation
    "navigation_depth": 4,
    "collapse_navigation": True,  # Collapse navigation by default
    "sticky_navigation": True,  # Fixed sidebar
    "titles_only": False,
    "prev_next_buttons_location": "bottom",
    # External Links
    "style_external_links": True,  # Add external link icon
}

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Intersphinx settings
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "click": ("https://click.palletsprojects.com/en/stable/", None),
    "libtorrent": ("https://www.libtorrent.org/python_binding.html", None),
}

# AutoDoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
    "show-inheritance": True,
}

# Add mock imports for external dependencies
autodoc_mock_imports = ["libtorrent", "click"]

# Coverage settings
coverage_show_missing_items = True

# ViewCode settings
viewcode_follow_imported_members = True

# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    # Paper size ('letterpaper' or 'a4paper')
    "papersize": "a4paper",
    # Font size ('10pt', '11pt' or '12pt')
    "pointsize": "11pt",
    # Additional LaTeX packages
    "preamble": r"""
        \usepackage{charter}
        \usepackage{inconsolata}
    """,
}

# Grouping the document tree into LaTeX files
latex_documents = [
    (
        "index",  # source start file
        "TorrentDirectories.tex",  # target name
        "TorrentDirectories Documentation",  # title
        author,  # author
        "manual",  # documentclass
    ),
]
