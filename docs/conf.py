# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
from typing import List

sys.path.insert(0, os.path.abspath(".."))

project = "TorrentDirectories"
copyright = "2025, friedhardware"
author = "friedhardware"

version = "1.0"
release = "1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
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
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True

# Intersphinx settings
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# AutoDoc settings
autodoc_member_order = "bysource"
autodoc_typehints = "description"
add_module_names = False
