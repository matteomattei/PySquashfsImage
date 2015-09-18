#!/usr/bin/env python

from setuptools import setup,find_packages

setup(
	name='PySquashfsImage',
	version='0.3',
	description='Squashfs image parser',
	long_description='This package provides a way to read and extract squashfs images.',
	author='Matteo Mattei; Nicola Ponzeveroni;',
	author_email='info@matteomattei.com; nicola.ponzeveroni@gilbarco.com;',
	url='https://github.com/matteomattei/PySquashfsImage',
	packages=find_packages(),
	keywords = ["filesystem", "parser", "squash", "squashfs"],
	classifiers = [
		"Programming Language :: Python",
		"Programming Language :: Python :: 3",
		"Development Status :: 4 - Beta",
		"Environment :: Other Environment",
		"Intended Audience :: Developers",
		"License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
		"Operating System :: OS Independent",
		"Topic :: Software Development :: Libraries :: Python Modules",
		],
)

