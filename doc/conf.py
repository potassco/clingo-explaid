# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import configparser
import datetime
import os

# modules that autodock should mock
# useful if some external dependencies are not satisfied at doc build time.
autodoc_mock_imports = []

# -- Project information -----------------------------------------------------

_config = configparser.RawConfigParser()
_config.read(os.path.join("..", "setup.cfg"))
_meta = dict(_config.items("metadata"))

project = _meta["name"]
copyright = f'{datetime.datetime.now().date().strftime("%Y")}, {_meta["author"]}'
author = _meta["author"]

# The full version, including alpha/beta/rc tags
release = _meta["version"]

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones. Make sure that custom extensions are listed in the doc field of
# [options.extras_require] in setup.cfg so they are available when building
# the documentation.

extensions = [
    "nbsphinx",
    "sphinx_rtd_theme",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
]

autosummary_generate = True

# intersphinx_mapping = {'clorm': ('https://clorm.readthedocs.io/en/latest/', None)}

# napoleon_google_docstring = False
# napoleon_use_ivar = True
napoleon_include_init_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_references = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

html_theme_options = {
    "canonical_url": "",
    #    'analytics_id': 'UA-XXXXXXX-1',  #  Provided by Google in your dashboard
    "logo_only": False,
    "display_version": True,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    # Toc options
    "collapse_navigation": True,
    "sticky_navigation": False,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']
