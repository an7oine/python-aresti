# -*- coding: utf-8 -*-

from setuptools import setup

setup(
  setup_requires='git-versiointi',
  name='python-aresti',
  description='Asynkroninen REST-rajapintayhteystoteutus',
  url='https://github.com/an7oine/python-aresti.git',
  author='Antti Hautaniemi',
  author_email='antti.hautaniemi@pispalanit.fi',
  licence='MIT',
  py_modules=['aresti'],
  install_requires=['aiohttp'],
)
