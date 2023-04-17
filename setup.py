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
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={
        "console_scripts": [
            "pysquashfsimage = PySquashfsImage.PySquashfsImage:main",
        ]
    }
)
