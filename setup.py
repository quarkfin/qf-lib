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
    version='1.1',
    author='Jacek Witkowski, Marcin Borratynski, Thomas Ruxton, Dominik Picheta, Olga Kalinowska, Karolina Cynk, '
           'Jakub Czerski, Bartlomiej Czajewski',
    description='Quantitative Finance Library',
    long_description=long_description,
    license='Apache License 2.0',
    long_description_content_type="text/markdown",
    project_urls={
        'Documentation': 'https://quarkfin.github.io/qf-lib/',
        'Source': 'https://github.com/quarkfin/qf-lib',
        'Tutorials': 'https://quarkfin.github.io/qf-lib-info/'
    },
    classifiers=[
        'Development Status :: 4 - Beta'
        'Programming Language :: Python :: 3.9',
    ],
    url='https://quarkfin.github.io/qf-lib/',
    packages=find_packages(include=('qf_lib', 'qf_lib_tests')),
    provides=[
        'qf_lib'
    ],
    include_package_data=True,
    install_requires=[
        'certifi==2020.12.5',
        'pandas==1.2.4',
        'numpy>=1.19.0,<1.21.0',
        'scipy==1.6.3',
        'matplotlib==3.4.2',
        'scikit-learn==0.24.2',
        'cvxopt==1.2.7',
        'openpyxl==3.0.7',
        'Pillow==8.2.0',
        'WeasyPrint==52.5',
        'emails==0.6',
        'Jinja2==2.11.3',
        'arch==4.19',
        'beautifulsoup4==4.9.3',
        'joblib==1.0.1',
        'quandl==3.6.1',
        'requests==2.25.1',
        'seaborn==0.11.1',
        'statsmodels==0.12.2',
        'xarray==0.18.0',
        'dic==1.5.2b1',
        'patsy==0.5.1',
        'tqdm==4.51.0',
        'xlrd==1.1.0'
    ],
    extras_require={
        "documentation": ["autodocsumm==0.1.13", "sphinx_rtd_theme==0.5.0", "Sphinx==3.1.1"],
        "interactive brokers": ["ibapi"],
        "bloomberg_beap_hapi": ["PyJWT>=0.2.3,<2.0.0", "retrying==1.3.3"]
    },
    keywords='quantitative finance backtester',
    python_requires='>=3.9.0'
)
