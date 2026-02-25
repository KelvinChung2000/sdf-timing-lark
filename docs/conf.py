"""Sphinx configuration for sdf-timing documentation."""

project = "sdf-timing"
copyright = "2024, F4PGA Authors"
author = "F4PGA Authors"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.doctest",
]

autodoc_member_order = "bysource"
napoleon_numpy_docstring = True
myst_enable_extensions = ["colon_fence", "fieldlist"]

html_theme = "sphinx_rtd_theme"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}
