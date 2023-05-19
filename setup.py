#!/usr/bin/env python

from io import open  # Remove this import when dropping Python 2 support
from setuptools import setup, find_packages

with open("README.md", 'r', encoding="utf8") as f:
    long_description = f.read()

setup(
    name='PySquashfsImage',
    version='0.8.0',
    description='Squashfs image parser',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Matteo Mattei; Nicola Ponzeveroni;',
    author_email='info@matteomattei.com',
    url='https://github.com/matteomattei/PySquashfsImage',
    packages=find_packages(),
    keywords=["filesystem", "parser", "squash", "squashfs"],
    python_requires=">=2.7",
    install_requires=[
        "argparse;python_version>='3.0' and python_version<'3.2'",
        "enum34;python_version<'3.4'"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={
        "console_scripts": [
            "pysquashfsimage = PySquashfsImage.__main__:main",
        ]
    }
)
