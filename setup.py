#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='qf-lib',
    version='1.0.0',
    author='Jacek Witkowski, Marcin Borratynski, Thomas Ruxton, Dominik Picheta, Olga Kalinowska, Karolina Cynk',
    author_email='qf-lib@cern.ch',
    description='Quantitative Finance Library',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://quarkfin.github.io/qf-lib/',
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
        'Source': 'https://github.com/quarkfin/qf-lib'
    },
    python_requires='>=3.6.0'
)
