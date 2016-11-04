from setuptools import setup
import re

version = ''
with open('tjson.py') as f:
    version = re.search(r'__version__\s*=\s*\'(.+)\'', f.read()).group(1)

if not version:
    raise RuntimeError("Couldn't find version string")

with open('README.md', 'r') as f:
    readme = f.read()

setup(
    name='tjsonpy',
    version=version,
    url='https://github.com/nickfrostatx/tjson-python',
    author='Nick Frost',
    author_email='nickfrostatx@gmail.com',
    description='Tagged JSON with Rich Types',
    long_description=readme,
    py_modules=['tjson'],
    keywords=['tjson'],
)
