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
           'Jakub Czerski, Bartlomiej Czajewski, Octavian Matei',
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
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.7',
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
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
        "documentation": ["autodocsumm==0.1.13", "sphinx_rtd_theme==0.5.0", "Sphinx==3.1.1"],
        "interactive brokers": ["ibapi"],
        "bloomberg_beap_hapi": ["PyJWT>=0.2.3,<2.0.0", "retrying>=1.3.3", "beap-lib==0.0.1"],
        "blpapi": ["blpapi>=3.16.2,<3.18.0"]
    },
    keywords='quantitative finance backtester',
    python_requires='>=3.7.1'
)
