#!/bin/bash

python setup.py clean check build sdist bdist bdist_egg build_sphinx register upload_docs upload -r pypi
