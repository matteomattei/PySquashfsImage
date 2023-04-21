#!/bin/bash

python setup.py clean check build sdist bdist_egg bdist_wheel build_sphinx
twine upload dist/*
