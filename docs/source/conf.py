# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath('../..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '_ext'))

import qf_lib

# -- Project information -----------------------------------------------------

project = 'QF-Lib'
copyright = datetime.today().strftime("%Y") + ', CERN Pension Fund'

release = qf_lib.__version__


def _documentation_version_label(full_version: str) -> str:
    """Use a friendly label for non-tag (development) builds."""
    base = full_version.split('+')[0]
    if '+' not in full_version:
        return base
    suffix = full_version.split('+', 1)[1]
    # versioneer dev builds: 4.0.6+1.gd9ae462
    if re.match(r'^\d+\.g[a-f0-9]+$', suffix, re.IGNORECASE):
        return 'Latest release'
    return base


_docs_version_label = _documentation_version_label(release)
version = '.'.join(release.split('+')[0].split('.')[:2])


# -- General configuration ---------------------------------------------------

extensions = [
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx_copybutton',
]

# Anchors for version headings in release_notes_generated.md (e.g. release-v4-0-6)
myst_heading_anchors = 3

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
html_title = f'{project} ({_docs_version_label})'
html_theme_options = {
    'show_nav_level': 1,
    'show_toc_level': 2,
    'navigation_depth': 4,
    'collapse_navigation': False,
    'navigation_with_keys': True,
    'navbar_align': 'left',
    'logo_text': f'{project} ({_docs_version_label})',
    'pygments_light_style': 'default',
    'pygments_dark_style': 'native',
    'icon_links': [
        {
            'name': 'GitHub',
            'url': 'https://github.com/quarkfin/qf-lib',
            'icon': 'fa-brands fa-github',
        },
        {
            'name': 'Discord',
            'url': 'https://discord.gg/CfMf8zaeX9',
            'icon': 'fa-brands fa-discord',
        },
    ],
    'footer_icons': [
        {
            'name': 'GitHub',
            'url': 'https://github.com/quarkfin/qf-lib',
            'html': '',
            'class': 'fa-brands fa-github',
        },
        {
            'name': 'Discord',
            'url': 'https://discord.gg/CfMf8zaeX9',
            'html': '',
            'class': 'fa-brands fa-discord',
        },
    ],
}

html_static_path = ['_static']
html_css_files = [
    'theme_overrides.css',
    'home.css',
]

# -- sphinx-copybutton -------------------------------------------------------

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
autodoc_mock_imports = ["cvxopt", "ibapi", "blpapi", "PyJWT", "retrying", "beap_lib", "jwt",
                        "cryptography", "fastparquet", "oauthlib", "requests_oauthlib", "urllib3"]
html_show_sourcelink = False


def setup(app):
    """Generate release notes from GitHub before each documentation build."""

    from _ext.release_notes import generate_release_notes

    generate_release_notes(app.confdir)
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
