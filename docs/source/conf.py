# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
#sys.path.insert(0, os.path.abspath('../../pyfea'))

abspath = os.path.abspath('../..')
print(os.path.abspath(abspath))
sys.path.insert(0, abspath)

# -- Project information -----------------------------------------------------

project = 'pyFEA'
copyright = '2019, Christophe Foyer'
author = 'Christophe Foyer'

# The full version, including alpha/beta/rc tags
release = '0.0.1'

html_logo = '_static/pyfea_text.jpg'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinxcontrib.fulltoc', 'sphinxjp.themes.basicstrap', 'sphinx.ext.autodoc']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'basicstrap'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

autodoc_default_options = {
    'member-order': 'groupwise',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}
