import sys, os

project = "line-uds"
copyright = "Balazs Eszes, 2024"
author = "Balazs Eszes"
version = '0.1'

sys.path.append(os.path.abspath("./_ext"))
sys.path.append(os.path.abspath("../python-lib"))

extensions = [
    "sphinx_rtd_theme",
    'jupyter_sphinx',
    'sphinx.ext.mathjax',
    'matplotlib.sphinxext.mathmpl',
    'matplotlib.sphinxext.plot_directive',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.doctest',
    'sphinxcontrib.mermaid',
    'sphinxcontrib.kroki'
]

autosectionlabel_prefix_document = True

autoclass_content = "init"

html_static_path = ['_static']
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation" : False,
    "show_navbar_depth": 2
}
html_js_files = ["https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"]
source_suffix = '.rst'
master_doc = 'index'
