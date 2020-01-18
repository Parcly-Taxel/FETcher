#!/usr/bin/env python3.7
from setuptools import setup, find_packages

with open('readme.md') as f:
    readme = f.read()
with open('licence') as f:
    licence = f.read()

setup(
    name='fetcher',
    version='1.0.0',
    description='Python file transfer between Git repositories',
    long_description=readme,
    author='Jeremy Tan Jie Rui',
    author_email='reddeloostw@gmail.com',
    url='https://github.com/Parcly-Taxel/fetcher',
    license=licence,
    packages=find_packages(exclude=('tests', 'docs'))
)
