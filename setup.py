#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
      name='triagelib',
      version='1.0.0',
      author='Jacob Blackburn',
      license='MIT',
      url='https://github.com/jblackb1/triagelib',
      description='Cofense Triage REST API wrapper',
      long_description=open('README.md').read(),
      packages=find_packages()
      )
