from setuptools import setup

setup(
    # name of the installed package
    name='qf-lib',
    version='1.0',
    description='Quantitative Finance Library',
    author='Jacek Witkowski, Marcin Borratynski, Thomas Ruxton, Dominik Picheta',
    author_email='qf-lib@cern.ch',
    url='https://gitlab.cern.ch/pfreport/QF-Lib',
    packages=[
        'qf_lib'
    ],
    provides=[
        'qf_lib'
    ],
    install_requires=[
        'numpy',
        'pandas',
        'emails',
        'Jinja2',
        'scipy',
        'matplotlib',
        'seaborn',
        'scikit-learn',
        'blpapi',
        'bs4',
        'quandl',
        'weasyprint',
        'openpyxl',
        'xlrd',
        'statsmodels',
        'arch',
        'mockito'
    ],
    keywords='quantitative finance backtester',
    project_urls={
        'Bug Reports': 'https://gitlab.cern.ch/pfreport/QF-Lib/issues',
        'Source': 'https://gitlab.cern.ch/pfreport/QF-Lib'
    },
    python_requires='>=3.5.3'
)
