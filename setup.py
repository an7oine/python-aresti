# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
  setup_requires='git-versiointi>=1.6rc3',
  name='python-aresti',
  description='Asynkroninen REST-rajapintayhteystoteutus',
  url='https://github.com/an7oine/python-aresti.git',
  author='Antti Hautaniemi',
  author_email='antti.hautaniemi@pispalanit.fi',
  licence='MIT',
  packages=find_packages(),
  install_requires=['aiohttp'],
)
