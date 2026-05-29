# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath('../..'))

import qf_lib

# -- Project information -----------------------------------------------------

project = 'QF-Lib'
copyright = datetime.today().strftime("%Y") + ', CERN Pension Fund'

release = qf_lib.__version__
version = '.'.join(release.split('+')[0].split('.')[:2])


# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx_copybutton',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
}

templates_path = ['_templates']
pygments_style = 'default'

exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

html_theme = "pydata_sphinx_theme"
html_theme_options = {
    'show_nav_level': 1,
    'show_toc_level': 2,
    'navigation_depth': 4,
    'collapse_navigation': False,
    'navigation_with_keys': True,
    'navbar_align': 'left',
    'logo_text': 'QF-Lib',
    'pygments_light_style': 'default',
    'pygments_dark_style': 'native',
}

html_static_path = ['_static']
html_css_files = [
    'theme_overrides.css',
]

# -- sphinx-copybutton -------------------------------------------------------

# Strip shell/Python REPL prompts when copying; leave full blocks without prompts unchanged.
copybutton_prompt_text = (
    r">>> |\.\.\. "
    r"|\$ "
    r"|In \[\d*\]: "
    r"| {2,5}\.\.\.: "
    r"| {5,8}: "
)
copybutton_only_copy_prompt_lines = False
copybutton_remove_prompts = True

# -- Extension configuration -------------------------------------------------

autosummary_generate = True
autodoc_mock_imports = ["cvxopt", "ibapi", "blpapi", "PyJWT", "retrying", "beap_lib"]
html_show_sourcelink = False
