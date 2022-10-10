# Creates executable from specified .py file

from distutils.core import setup
import py2exe

setup(console=['main.py'])
