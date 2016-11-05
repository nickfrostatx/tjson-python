# tjson

[![Build Status](https://travis-ci.org/nickfrostatx/tjson-python.svg?branch=master)](https://travis-ci.org/nickfrostatx/tjson-python)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/nickfrostatx/tjson-pythons/master/LICENSE)

> Tagged JSON with Rich Types

Installation
------------

```bash
$ pip install tjsonpy
```

Usage
-----

```python
>>> import tjson
>>> tjson.parse('{"s:foo":"i:bar"}')
{'foo': 'bar'}
>>> tjson.dumps({'foo': 'bar'})
'{"s:foo": "s:bar"}'
```
