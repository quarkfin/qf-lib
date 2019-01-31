from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='qf-lib',
    version='1.0.0',
    author='Jacek Witkowski, Marcin Borratynski, Thomas Ruxton, Dominik Picheta, Olga Kalinowska',
    author_email='qf-lib@cern.ch',
    description='Quantitative Finance Library',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://gitlab.cern.ch/pfreport/QF-Lib',
    packages=find_packages(),
    provides=[
        'qf_lib'
    ],
    include_package_data=True,
    install_requires=[
        'numpy',
        'scipy',
        'dic',
        'matplotlib',
        'openpyxl',
        'pandas',
        'scikit-learn',
        'xlrd',
        'emails',
        'Jinja2',
        'weasyprint',
        'seaborn',
        'statsmodels',
        'arch',
        'quandl',
        'beautifulsoup4',
        'mockito',
        'xarray',
        'cvxopt'
    ],
    keywords='quantitative finance backtester',
    project_urls={
        'Bug Reports': 'https://gitlab.cern.ch/pfreport/QF-Lib/issues',
        'Source': 'https://gitlab.cern.ch/pfreport/QF-Lib'
    },
    python_requires='>=3.6.0'
)
