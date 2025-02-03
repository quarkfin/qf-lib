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

from setuptools import setup
import versioneer

with open("README.md", "r") as fh:
    long_description = fh.read()
with open("requirements.txt", "r") as fh:
    requirements = [line.strip() for line in fh]

setup(
    name='qf-lib',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author='Jacek Witkowski, Marcin Borratynski, Thomas Ruxton, Dominik Picheta, Olga Kalinowska, Karolina Cynk, '
           'Jakub Czerski, Bartlomiej Czajewski, Zeynep Gültuğ Aydemir, Octavian-Mihai Matei, Eirik Thorp Eythorsson, '
           'Marek Bais',
    description='Quantitative Finance Library',
    long_description=long_description,
    license='Apache License 2.0',
    long_description_content_type="text/markdown",
    project_urls={
        'Documentation': 'https://qf-lib.readthedocs.io',
        'Source': 'https://github.com/quarkfin/qf-lib',
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        'Topic :: Office/Business :: Financial',
        'Topic :: Scientific/Engineering :: Information Analysis',
    ],
    url='https://quarkfin.github.io/qf-lib-info',
    packages=['qf_lib'],
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        "documentation": ["autodocsumm==0.2.9", "sphinx_rtd_theme==1.2.0", "Sphinx==5.0", "docutils==0.18.1", "markupsafe==2.0.1"],
        "interactive brokers": ["ibapi"],
        "bloomberg_beap_hapi": ["PyJWT>=0.2.3,<2.0.0", "retrying>=1.3.3", "beap-lib==0.0.1", "requests>=2.25.1,<=2.31.0"],
        "blpapi": ["blpapi>=3.21.0,<=3.24.4"],
        "quandl": ["quandl>=3.6.1,<=3.7.0"],
        "yfinance": ["yfinance>=0.2.50"],
        "detailed_analysis": ["statsmodels>=0.13.0,<0.14.0", "scipy>=1.6.3 ,<1.12.0", "cvxopt>=1.2.7,<=1.3.2",
                              "arch>=5.4,<=7.0"]
    },
    keywords='quantitative finance backtester',
    python_requires='>=3.8.0'
)
